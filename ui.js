let settingsBaseline=null;
let activeSettingsPanel=null; // 'upper' or 'lower'
let lowerSettingsVisible=false;
let lowerOpenGroups=new Set();
let activeTabMenuId=null;
function captureSettingsDraft(){
 saveActiveMealPlan();
 return JSON.stringify({weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters,weekdayColors,pinnedCats,expandedCats,autoPinTopCategories,applyPinsToAllTabs,timeDisplayPrefs,mealTextSize,showLastCooked,showMakeAheadReminders:makeAheadDisplayPrefs.showMakeAheadReminders,manualRecipeOrdering,showMealPlanTabs,mealPlans,activePlanId,startWeekday,masterOpenMode,masterPinsOverride});
}
function restoreSettingsDraft(json){
 if(!json)return;
 const state=JSON.parse(json);
 makeAheadDisplayPrefs.showMakeAheadReminders=state.showMakeAheadReminders!==false;saveMakeAheadDisplayPrefs();
 if(['normal','large','extra'].includes(state.mealTextSize)){mealTextSize=state.mealTextSize;localStorage.setItem(mealTextSizeKey,mealTextSize);applyMealTextSize()}
 weekdayCategories=JSON.parse(JSON.stringify(state.weekdayCategories));weekdayMealOverrides={...state.weekdayMealOverrides};weekdayRecipeFilters=JSON.parse(JSON.stringify(state.weekdayRecipeFilters||{}));
 weekdayColors={...state.weekdayColors};pinnedCats=[...state.pinnedCats];expandedCats=[...state.expandedCats];
 autoPinTopCategories=true;applyPinsToAllTabs=!!state.applyPinsToAllTabs;timeDisplayPrefs=JSON.parse(JSON.stringify(state.timeDisplayPrefs));
 manualRecipeOrdering=state.manualRecipeOrdering===true;saveManualRecipeOrdering();
 showLastCooked=state.showLastCooked!==false;saveLastCookedVisibility();showMealPlanTabs=!!state.showMealPlanTabs;if(['all','current','across','none'].includes(state.masterOpenMode))masterOpenMode=state.masterOpenMode;masterPinsOverride=state.masterPinsOverride!==false;saveMasterOpeningPrefs();mealPlans=JSON.parse(JSON.stringify(state.mealPlans));activePlanId=state.activePlanId;startWeekday=state.startWeekday;autoPinTopCategories=true;
 try{
 localStorage.setItem('mealRotationWeekdayCategoriesV1',JSON.stringify(weekdayCategories));
 localStorage.setItem('mealRotationWeekdayMealOverridesV1',JSON.stringify(weekdayMealOverrides));
 localStorage.setItem(weekdayRecipeFiltersKey,JSON.stringify(weekdayRecipeFilters));
 localStorage.setItem('mealRotationWeekdayColorsV1',JSON.stringify(weekdayColors));
 localStorage.setItem('mealRotationPinnedCategoriesV1',JSON.stringify(pinnedCats));
 localStorage.setItem('mealRotationExpandedCategoriesV1',JSON.stringify(expandedCats));
 localStorage.setItem('mealRotationAutoPinTopCategoriesV1',String(autoPinTopCategories));
 localStorage.setItem('mealRotationShowPlanTabsV1',String(showMealPlanTabs));
 localStorage.setItem('mealRotationStartWeekdayV1',startWeekday);
 }catch(e){}
 saveTimeDisplayPrefs();saveActiveMealPlan();
}
function settingsAreDirty(){return settingsBaseline!==null&&captureSettingsDraft()!==settingsBaseline}
async function finishSettings(mode='ask'){
 if(settingsBaseline===null)return true;
 const baseline=settingsBaseline;let keep=true;
 if(mode==='cancel')keep=false;
 else if(mode==='ask'&&settingsAreDirty())keep=await appDialog('Save settings changes?',null,'yesno')===true;
 settingsBaseline=null;
 const openPanel=document.getElementById('settingsPanel');if(openPanel)openPanel.classList.add('hidden');
 const lowerPanel=document.getElementById('planSettingsPanel');if(lowerPanel)lowerPanel.classList.add('hidden');
 lowerSettingsVisible=false;activeSettingsPanel=null;
 const settingsToggle=document.getElementById('settings');if(settingsToggle){settingsToggle.classList.remove('active');settingsToggle.setAttribute('aria-expanded','false')}
 const lowerToggle=document.getElementById('planSettings');if(lowerToggle){lowerToggle.classList.remove('active');lowerToggle.setAttribute('aria-expanded','false')}
 if(!keep)restoreSettingsDraft(baseline);
 return true;
}
// Browser history tracks views, not recipe edits or localStorage snapshots.
function appViewSnapshot(){return {view:!showTop?'groups':groceryTabActive?'grocery':allMealsActive?'all':'top',planId:activePlanId};}
function pushAppViewHistory(){
 const next=appViewSnapshot();
 const previous=window.history.state?.mealRotationView;
 if(previous&&(previous.view!==next.view||previous.planId!==next.planId)){
  window.history.pushState({mealRotationView:next},'');
 }
}
// Editor and its child dialogs consume Back before view navigation.
let editorHistoryClosing=false,editorBackBusy=false,editorHistorySettled=Promise.resolve(),resolveEditorHistory=null;
function stepEditorHistoryBack(){editorHistoryClosing=true;editorHistorySettled=new Promise(resolve=>resolveEditorHistory=resolve);window.history.back()}
const editorDialogStack=[];
function dismissEditorHistory(){
 if(window.history.state?.mealRotationEditor&&editId===null){stepEditorHistoryBack()}
}
async function closeMealEditorWithPrompt(){
 if(editId===null)return true;
 if(editorHasPendingChanges()){
  const save=await appDialog('Save meal changes before closing?',null,'yesnocancel');
  if(save===null)return false;
  if(save){const current=editId;await document.getElementById('save')?.onclick?.();await editorHistorySettled;return editId!==current}
 }
 if(editId!==null){mealPersistence.cancelOwner('recipe:'+editId);rollbackEditorCategories();editId=null;restoreMealEditorScroll()}await editorHistorySettled;return true;
}
window.addEventListener('popstate',event=>{
 if(editorHistoryClosing){editorHistoryClosing=false;resolveEditorHistory?.();resolveEditorHistory=null;event.stopImmediatePropagation();return}
 if(editId===null||recipeViewer||recipeEditorReturn||!mealEditorReturnView||mealEditorReturnView.view!=='groups')return;
 event.stopImmediatePropagation();const state={...window.history.state,mealRotationView:{view:'groups',planId:activePlanId},mealRotationEditor:String(editId)};
 const child=editorDialogStack.at(-1),active=document.activeElement,keyboard=active?.matches('input:not([type=checkbox]),textarea')&&(document.querySelector('#editor .meal-editor-keyboard-open')||innerHeight-(window.visualViewport?.height||innerHeight)>120);
 if(keyboard){window.history.pushState(child?{...state,mealRotationEditorDialog:child.id}:state,'');active.blur();return}
 const modal=[...document.querySelectorAll('[aria-modal=true]')].filter(el=>!el.closest('[inert]')&&el.getClientRects().length).at(-1);
 if(modal&&(!child||!child.overlay.contains(modal))&&!editorBackBusy){window.history.pushState(child?{...state,mealRotationEditorDialog:child.id}:state,'');const cancel=modal.querySelector('button[aria-label^=Cancel],button[aria-label^=Close],button[aria-label=No]');if(cancel)cancel.click();else modal.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));return}
 if(child){child.close(true);return}
 if(editorBackBusy){window.history.pushState(state,'');const prompt=[...document.querySelectorAll('[role=dialog]')].find(dialog=>dialog.textContent.includes('Save meal changes before closing?'));prompt?.querySelector('button[aria-label=Cancel]')?.click();return}
 if(editorHasPendingChanges())window.history.pushState(state,'');
 editorBackBusy=true;closeMealEditorWithPrompt().finally(()=>{editorBackBusy=false});
},true);
window.addEventListener('popstate',event=>{
 const destination=event.state?.mealRotationView;
 if(!destination)return;
 if(destination.planId!==activePlanId&&mealPlans.some(p=>p.id===destination.planId))loadMealPlan(destination.planId);
 showTop=destination.view!=='groups';
 groceryTabActive=destination.view==='grocery';
 allMealsActive=destination.view==='all';
 if(!showTop)initializeMasterCategoryExpansion();
 editId=null;menuCat=null;activeTabMenuId=null;
 render();window.scrollTo(0,0);
});
async function navigateAfterSettings(callback){
 if(settingsBaseline!==null){await finishSettings('ask');render();}
 callback();
 pushAppViewHistory();
}
function makeSettingsGroup(key,title){
  const details=document.createElement('details');details.className='settings-group';details.dataset.settingsGroup=key;
  const summary=document.createElement('summary');summary.textContent=title;
  const chevron=document.createElementNS('http://www.w3.org/2000/svg','svg');
  chevron.setAttribute('class','settings-chevron');
  chevron.setAttribute('viewBox','0 0 24 24');
  chevron.setAttribute('aria-hidden','true');
  chevron.innerHTML='<path d="m6 9 6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/>';
  summary.append(chevron);
  const content=document.createElement('div');content.className='settings-group-content';
  details.append(summary,content);return {details,content};
}
// Short settings groups stay open rather than requiring an extra chevron.
function settingsFlatGroup(title){
 const wrap=document.createElement('div');wrap.className='settings-flat-group';
 const heading=document.createElement('strong');heading.textContent=title;
 const body=document.createElement('div');body.className='settings-flat-content';
 wrap.append(heading,body);return {wrap,body};
}
function populateCookedDateSetting(parent){
 const label=document.createElement('label');label.className='settings-display-option';
 const check=document.createElement('input');check.type='checkbox';check.checked=showLastCooked;
 check.onchange=()=>{showLastCooked=check.checked;saveLastCookedVisibility();renderList()};
 label.append(check,document.createTextNode('Show last cooked dates'));parent.append(label);
}
function populateTimeSettings(parent){
 for(const [field,title] of [['cooking','Show cooking times'],['marinate','Show marinade time']]){
  const label=document.createElement('label');label.className='settings-display-option';
  const check=document.createElement('input');check.type='checkbox';
  check.checked=timeDisplayPrefs[showTop?(allMealsActive?'all':'top'):'category'][field];
  check.onchange=()=>{timeDisplayPrefs[showTop?(allMealsActive?'all':'top'):'category'][field]=check.checked;saveTimeDisplayPrefs();renderList()};
  label.append(check,document.createTextNode(title));parent.append(label);
 }
}
function makeSettingsFooter(){
 const footer=document.createElement('div');footer.className='settings-footer';
 const save=document.createElement('button');save.type='button';
 setIconButton(save,'save','Save settings');
 save.onclick=async()=>{await finishSettings('save');render()};
 const cancel=document.createElement('button');cancel.type='button';
 setIconButton(cancel,'cancel','Cancel settings');
 cancel.onclick=async()=>{await finishSettings('cancel');render()};
 footer.append(save,cancel);return footer;
}
// The cart is a temporary tab, not a new meal plan or a popup.

function navigateToOverviewPlan(planId){loadMealPlan(planId);window.scrollTo({top:0,behavior:'instant'})}
function navigateToOverviewMeal(planId,mealId){
 // Open the selected meal inside its group, rather than returning to My Rotation.
 const meal=meals.find(m=>String(m.id)===String(mealId));
 if(!meal)return;
 loadMealPlan(planId);
 openMasterCategories(meal.cat);

}
function addOverviewHomeButton(){
 if(!showTop||!(groceryTabActive||allMealsActive))return;
 const b=document.createElement('button');b.type='button';b.className='smallbtn add-meal-floating overview-home-fab';b.title='Return to My Rotation';b.setAttribute('aria-label',b.title);
 b.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true" style="width:27px;height:27px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linejoin:round"><path d="M3 10.2 12 3l9 7.2V21h-6.5v-7h-5v7H3z"/></svg>';
 b.onclick=()=>{groceryTabActive=false;allMealsActive=false;renderList()};document.body.append(b);
}
let overviewWeekOffset=0,rotationWeekOffset=0;
function weekSelector(offset,onChange){
 const row=document.createElement('div');row.className='week-selector';row.setAttribute('role','group');row.setAttribute('aria-label','Displayed week');
 for(const [value,label]of [[0,'This week'],[1,'Next week']]){const button=document.createElement('button');button.type='button';button.textContent=label;button.setAttribute('aria-pressed',String(offset===value));button.onclick=()=>onChange(value);row.append(button)}return row;
}
function rotationWeekControls(existing=[]){
 const controls=document.createElement('div');controls.className='rotation-heading-actions rotation-week-controls';
 for(const [index,label,path]of [[0,'Rotate Meals','M12 4v12m-5-5 5 5 5-5M5 20h14'],[1,'Rotate Back','M12 20V8m-5 5 5-5 5 5M5 4h14']]){
  const button=existing[index]||document.createElement('button');button.type='button';button.classList.add('iconbtn','rotation-labeled-button');button.style.cssText='';button.disabled=!!rotationWeekOffset||!existing[index];button.title=label;button.setAttribute('aria-label',label);
  if(!existing[index])button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="'+path+'" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const text=document.createElement('span');text.className='rotation-button-label';text.textContent=label;button.append(text);controls.append(button);
 }
 const toggle=document.createElement('button');toggle.type='button';toggle.className='iconbtn rotation-labeled-button rotation-week-toggle';const label=rotationWeekOffset?'This week':'Next week';setIconButton(toggle,rotationWeekOffset?'left':'right',label);toggle.style.cssText='';const text=document.createElement('span');text.textContent=label;toggle.append(text);toggle.onclick=()=>{rotationWeekOffset=rotationWeekOffset?0:1;renderList()};controls.append(toggle);return controls;
}
function renderRotationWeekPreview(list){
 const upcoming=previewNextWeekPlans(),source=upcoming.find(item=>item.plan.id===activePlanId),heading=document.createElement('h2');heading.className='view-page-title';heading.textContent=(source?.plan.name?.trim()?'My '+source.plan.name.trim()+' Rotation':'My Rotation')+' · Next week';const header=document.createElement('div');header.className='rotation-compact-header';header.append(heading,rotationWeekControls());list.append(header);
 if(!source)return;const start=cookingPlanningWeekStart();start.setDate(start.getDate()+7);const tasks=makeAheadDisplayPrefs.showMakeAheadReminders?scheduledMakeAheadTasks(true,upcoming).filter(item=>item.plan.id===activePlanId):[];
 for(const day of orderedDays()){
  const date=cookingLocalDate(cookingDateInWeek(day,start)),card=document.createElement('section');card.className='all-meals-day';card.dataset.date=date;card.style.backgroundColor=colorForDay(day);
  const title=document.createElement('h3');title.textContent=day+' · '+parseCookingLocalDate(date).toLocaleDateString(undefined,{month:'short',day:'numeric'});card.append(title);
  const entries=source.entries.filter(entry=>entry.day===day&&cookingLocalDate(scheduledOccurrenceDate({...entry,planId:source.plan.id},source.plan.rotationCalendar))===date);
  if(!entries.length){const empty=document.createElement('div');empty.className='muted';empty.textContent='—';card.append(empty)}
  for(const entry of entries){const row=document.createElement('div');row.className='meal';const name=document.createElement('button');name.type='button';name.className='mealname';name.textContent=entry.meal.name;name.onclick=()=>openSavedMealRecipe(meals.find(meal=>String(meal.id)===String(entry.meal.id))||entry.meal);row.append(name);card.append(row)}
  appendMakeAheadDay(card,day,tasks,start);list.append(card);
 }
}
function previewNextWeekPlans(){
 const saved={meals,mealPlans,weekdayMealOverrides,storage:bulkRecipeStorageDraft};
 const nextStart=cookingPlanningWeekStart();nextStart.setDate(nextStart.getDate()+7);
 try{
  meals=JSON.parse(JSON.stringify(meals));mealPlans=JSON.parse(JSON.stringify(mealPlans));weekdayMealOverrides={...weekdayMealOverrides};
  bulkRecipeStorageDraft=new Map(Array.from({length:localStorage.length},(_,i)=>{const key=localStorage.key(i);return [key,localStorage.getItem(key)]}));
  const slots=new Set();for(const plan of mealPlans)for(const item of rotationSelectionEntries(plan)){
   const date=scheduledOccurrenceDate({...item,planId:plan.id},plan.rotationCalendar,new Date());if(!date||date<nextStart)slots.add(plan.id+'||'+weekdaySlotKey(item.day,item.cat));
  }
  moveDisplayedMealsToBottom(slots,true,false,null,null,true);if(hasDependentSideSlots())coordinateDependentSides();
  return mealPlans.map(plan=>{
   const entries=getDisplayedWeekdayMealsForPlan(plan),calendar=rotationCalendarForPlan(plan,entries);
   for(const entry of entries){const key=rotationOccurrenceKey({...entry,planId:plan.id});const target=cookingDateInWeek(entry.day,nextStart),stored=parseCookingLocalDate(calendar.occurrences[key]);calendar.occurrences[key]=cookingLocalDate(stored&&stored>target?stored:target);calendar.assignedOn[key]=cookingLocalDate(nextStart);calendar.assignedAt[key]='preview'}
   return {plan:{...plan,rotationCalendar:calendar},entries,preview:true};
  });
 }finally{meals=saved.meals;mealPlans=saved.mealPlans;weekdayMealOverrides=saved.weekdayMealOverrides;bulkRecipeStorageDraft=saved.storage}
}
function renderAllMealsOverview(list){
  const section=document.createElement('section');section.className='all-meals-overview';
  section.setAttribute('aria-label','Weekly Overview weekly overview');
  const heading=document.createElement('h2');heading.textContent='Weekly Overview';section.append(heading);
  const current=mealPlans.map(plan=>({plan,entries:getDisplayedWeekdayMealsForPlan(plan)})),upcoming=previewNextWeekPlans(),start=cookingPlanningWeekStart();start.setDate(start.getDate()+overviewWeekOffset*7);
  section.append(weekSelector(overviewWeekOffset,value=>{overviewWeekOffset=value;renderList()}));
  const byPlan=overviewWeekOffset?upcoming:current,prepRows=makeAheadDisplayPrefs.showMakeAheadReminders?scheduledMakeAheadTasks(true,upcoming):[];
  let selected={};try{selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}')}catch(e){}
  const hideChecked=localStorage.getItem('mealRotationHideCheckedGroceriesV1')==='true';
  for(const day of orderedDays()){
   const card=document.createElement('section');card.className='all-meals-day';
   card.style.backgroundColor=colorForDay(day);
   const title=document.createElement('h3');const date=cookingLocalDate(cookingDateInWeek(day,start));card.dataset.date=date;title.textContent=day+' · '+parseCookingLocalDate(date).toLocaleDateString(undefined,{month:'short',day:'numeric'});card.append(title);
   for(const {plan,entries} of byPlan){
    const dayEntries=entries.filter(entry=>entry.day===day&&cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},plan.rotationCalendar))===date);
    if(!dayEntries.length){
      const empty=document.createElement('div');empty.className='all-meals-entry all-meals-empty';
      const label=document.createElement('strong');label.textContent=plan.name;label.style.cursor='pointer';label.setAttribute('role','link');label.tabIndex=0;label.onclick=()=>navigateToOverviewPlan(plan.id);label.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();label.click()}};
      const value=document.createElement('span');value.textContent='No meal planned';
      empty.append(label,value);card.append(empty);continue;
    }
    for(const {cat,meal,linkedTo} of dayEntries){
      const entry=document.createElement('div');entry.className='all-meals-entry';entry.dataset.mealId=String(meal.id);
      const row=document.createElement('div');row.className='all-meals-meal-row';
      const label=document.createElement('strong');label.className='all-meals-plan-label';
      label.textContent=plan.name;
      if(dayEntries.length>1){label.append(document.createElement('br'),document.createTextNode(cat));}
      const content=document.createElement('div');content.className='all-meals-meal-content';
      const name=document.createElement('button');name.type='button';name.className='mealname';name.textContent=meal.name;
      name.onclick=()=>navigateToOverviewMeal(plan.id,meal.id);
      content.append(name);bindRecipeTimerName(name,meal,linkedTo==null&&!dayEntries.some(parent=>parent.meal.id!==meal.id&&(parent.meal.linkedMealIds||[]).some(id=>String(id)===String(meal.id))));
      const times=mealTimeDescription(meal);if(times){const caption=document.createElement('div');caption.className='times';setTimeSegments(caption,times);content.append(caption)}
      label.style.cursor='pointer';label.setAttribute('role','link');label.tabIndex=0;
      label.onclick=()=>navigateToOverviewPlan(plan.id);
      label.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();label.click()}};
      row.append(label,content);entry.append(row);
      card.append(entry);
    }
   }
   appendMakeAheadDay(card,day,prepRows,start);section.append(card);
  }
  list.append(section);
}
// From an empty weekday, take the user directly to the relevant recipe group.
// Choosing a group here never changes the weekday assignment.
function openDayGroupForRotation(day){
 const assigned=getDayCategories(day);
 if(!assigned.length){openDayCategoryPicker(day);return;}
 const goToGroup=cat=>navigateAfterSettings(()=>openMasterCategories(cat));
 if(assigned.length===1){goToGroup(assigned[0]);return;}
 const shade=document.createElement('div');shade.style.cssText='position:fixed;inset:0;background:#0008;z-index:13000;display:grid;place-items:center;padding:18px';
 const panel=document.createElement('div');panel.style.cssText='background:#fff;border-radius:14px;padding:18px;width:min(420px,100%);max-height:80vh;overflow:auto';
 const heading=document.createElement('h3');heading.textContent='Which '+day+' meal group would you like to view?';heading.style.margin='0 0 12px';panel.append(heading);
 assigned.forEach(cat=>{const button=document.createElement('button');button.type='button';button.className='smallbtn';button.textContent=cat;button.style.cssText='display:block;width:100%;text-align:left;margin:8px 0;padding:12px';button.onclick=()=>{shade.remove();goToGroup(cat)};panel.append(button)});
 const cancel=document.createElement('button');cancel.type='button';cancel.className='iconbtn';setIconButton(cancel,'cancel','Cancel');cancel.onclick=()=>shade.remove();panel.append(cancel);
 shade.append(panel);shade.onclick=e=>{if(e.target===shade)shade.remove()};document.body.append(shade);
}
function openWeekdayCard(day){
 if(getDayCategories(day).length){openDayCategoryPicker(day);return}
 const shade=document.createElement('div');shade.style.cssText='position:fixed;inset:0;background:#0008;z-index:13000;display:grid;place-items:center;padding:18px';
 const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Plan '+day+"'s meal");panel.style.cssText='background:#fff;color:#242424;border-radius:14px;padding:18px;width:min(420px,100%);max-height:80vh;overflow-y:auto';
 appendRotationCloseHeader(panel,'Plan '+day+"'s meal",()=>shade.remove());
 for(const [label,action] of [['Select Meal',()=>{const current=getDisplayedWeekdayMeals().find(item=>item.day===day&&item.occasional&&!item.linkedTo);openWeekdayMealChooser(day,null,current?.meal,true)}],['Choose Meal Groups',()=>openDayCategoryPicker(day)]]){const button=document.createElement('button');button.type='button';button.className='smallbtn';button.textContent=label;button.style.cssText='display:block;width:100%;min-height:44px;padding:12px 14px;margin-top:10px;text-align:center';button.onclick=()=>{shade.remove();action()};panel.append(button)}
 shade.append(panel);shade.onclick=e=>{if(e.target===shade)shade.remove()};shade.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();shade.remove()}};document.body.append(shade);
}
function removeOccasionalMeal(day){
 const before=captureGroceryCheckStates();snapshot();const plan=mealPlans.find(plan=>plan.id===activePlanId),id=plan.occasionalMeals?.[day];delete plan.occasionalMeals?.[day];
 for(const [key,choice] of Object.entries(plan.cycleSlotChoices||{}))if(key.startsWith(day+'::')&&choice.occasional&&String(choice.mealId)===String(id)){delete weekdayMealOverrides[key];delete plan.cycleRetainedSlots?.[key];delete plan.cycleSlotChoices[key]}
 saveWeekdayMealOverrides();reconcileRotatedGroceryChecks(before,[]);persist();renderList();
}
function openDayCategoryPicker(day){
 const initiatingControl=document.activeElement,inert=[...document.body.children].map(el=>[el,el.inert]);
 const shade=document.createElement('div');shade.style.cssText='position:fixed;inset:0;background:#0008;z-index:13000;display:grid;place-items:center;padding:18px';
 const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-labelledby','weekdayGroupPickerTitle');panel.style.cssText='background:#fff;border-radius:14px;padding:18px;width:min(420px,100%);max-height:min(65vh,520px);overflow:hidden;display:flex;flex-direction:column';
 // Keep focus in the active picker even when assignment rendering replaces its opener.
 const focusable=()=>[...panel.querySelectorAll('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex="0"]')].filter(el=>el.getClientRects().length&&!el.closest('[inert]'));
 let closed=false;
 const containFocus=event=>{if(!closed&&!shade.inert&&!panel.contains(event.target))(focusable()[0]||panel).focus({preventScroll:true})};
 const dismiss=afterClose=>{if(closed)return;closed=true;document.removeEventListener('focusin',containFocus);if(activePlanId===pickerPlanId){const assigned=getDayCategories(day);if(unassignedWeekGroupSlots(mealPlans.find(p=>p.id===activePlanId),day,assigned).orphaned.length)setDayCategories(day,assigned.length?assigned:[EMPTY_DAY_ASSIGNMENT])}shade.remove();for(const [el,was]of inert)if(el.isConnected)el.inert=was;if(typeof afterClose==='function')afterClose();const usable=el=>el?.isConnected&&el.getClientRects().length&&!el.closest('[inert]');const dayControl=document.querySelector('button.weekday-heading[data-weekday="'+day+'"]'),target=usable(initiatingControl)&&initiatingControl!==document.body?initiatingControl:dayControl;if(usable(target))target.focus({preventScroll:true})};
 panel.tabIndex=-1;
 const heading=document.createElement('h3');heading.textContent='Choose '+day+"'s meal groups";heading.id='weekdayGroupPickerTitle';heading.style.cssText='margin:0;min-width:0;flex:1;overflow-wrap:anywhere';
 const header=document.createElement('div');header.style.cssText='display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-shrink:0';
 const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close');close.style.cssText+=';width:36px;height:36px;min-width:36px;min-height:36px;flex:0 0 36px';close.onclick=dismiss;header.append(heading,close);panel.append(header);
 const body=document.createElement('div');body.className='weekday-group-picker-body';body.style.cssText='overflow-y:auto;min-height:0;flex:1;overscroll-behavior:contain';panel.append(body);
 const pairBox=document.createElement('div');
 const renderChoices=()=>{
  body.replaceChildren();const assigned=getDayCategories(day);
  for(const cat of getCategoryButtonOrder()){
   const label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:10px;padding:4px;min-height:36px';
   const cb=document.createElement('input');cb.type='checkbox';cb.value=cat;cb.checked=assigned.includes(cat);cb.dataset.groupChoice='true';cb.style.width='20px';cb.style.height='20px';
   cb.addEventListener('change',()=>{if(activePlanId!==pickerPlanId)return;const selected=[...body.querySelectorAll('input[data-group-choice]:checked')].map(x=>x.value);setDayCategories(day,selected.length?selected:[EMPTY_DAY_ASSIGNMENT]);buildSidePairControls(pairBox,day);if(tutorialStage==='3'&&selected.length)setTutorialStage('done')});
   label.append(cb,document.createTextNode(cat));body.append(label);
  }
  body.append(pairBox);buildSidePairControls(pairBox,day);
 };
 const create=document.createElement('button');create.type='button';setIconButton(create,'add','Create New Group');create.style.cssText+=';width:44px;height:44px;min-width:44px;min-height:44px;flex:0 0 44px';header.insertBefore(create,close);
 const pickerPlanId=activePlanId;
 create.onclick=async()=>{
  if(create.disabled)return;create.disabled=true;shade.inert=true;
  try{
   const name=await appDialog('New group name','','prompt');if(name===null||name===false||closed||activePlanId!==pickerPlanId)return;
   const cat=createMealGroup(name);setDayCategories(day,[...getDayCategories(day),cat]);renderChoices();
  }catch(error){await showAppMessage(error.message)}
  finally{shade.inert=false;create.disabled=false;if(!closed)create.focus({preventScroll:true})}
 };
 renderChoices();
 shade.append(panel);shade.onclick=e=>{if(e.target===shade)dismiss()};
 shade.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();dismiss();return}if(e.key==='Tab'){const controls=focusable(),first=controls[0]||panel,last=controls.at(-1)||panel;if(!panel.contains(document.activeElement)||document.activeElement===panel||e.shiftKey&&document.activeElement===first||!e.shiftKey&&document.activeElement===last){e.preventDefault();(e.shiftKey?last:first).focus({preventScroll:true})}}};
 for(const [el]of inert)el.inert=true;document.body.append(shade);document.addEventListener('focusin',containFocus);close.focus({preventScroll:true});
}
function getVisibleTopMeals(){
 if(allMealsActive)return mealPlans.flatMap(plan=>getDisplayedWeekdayMealsForPlan(plan));
 if(groceryTabActive)return mealPlans.filter(plan=>!masterGroceryExcludedPlanIds.has(String(plan.id))).flatMap(plan=>getDisplayedWeekdayMealsForPlan(plan));
 return getDisplayedWeekdayMeals();
}
// A chosen first weekday can also reorder the pinned category buttons in
// this meal plan, without changing the global category order or other plans.
function getCategoryButtonOrder(){
 // Assigned categories follow the displayed weekday sequence; unassigned categories
 // retain their existing manual order. This does not mutate saved category data.
 const assigned=[];
 for(const day of orderedDays())for(const c of getDayCategories(day)){
  if(cats.includes(c)&&!assigned.includes(c))assigned.push(c);
 }
 return [...assigned,...cats.filter(c=>!assigned.includes(c))];
}
function rotatePinnedCategoriesToWeekdayOrder(){
 const plan=mealPlans.find(p=>p.id===activePlanId);
 if(!plan)return;
 const pinned=effectivePinnedCategories();
 const ordered=[];
 for(const day of orderedDays()){
  for(const category of getDayCategories(day)){
   if(pinned.has(category)&&!ordered.includes(category))ordered.push(category);
  }
 }
 // Retain manually pinned categories not associated with a weekday, followed
 // by unpinned categories, in the order they were displayed before.
 const existing=getCategoryButtonOrder();
 const remainder=existing.filter(c=>!ordered.includes(c));
 plan.pinnedDisplayOrder=[...ordered,...remainder];
 saveActiveMealPlan();
}
function splitPlanSettings(){return showTop&&showMealPlanTabs&&mealPlans.length>1}
function renderTabs(){let t=$('tabs');const previousRow=document.getElementById('categoryButtons');const oldCatMenu=document.getElementById('catmenu');if(oldCatMenu&&previousRow&&previousRow.contains(oldCatMenu))document.body.append(oldCatMenu);if(previousRow)previousRow.remove();const pageKey=showTop?'top-recipes':(masterCategoriesView?'master-groups':'group:'+active);const keepSettingsOpen=activeSettingsPanel==='upper'&&lastRenderedPageKey===pageKey&&!!t.querySelector('#settingsPanel:not(.hidden)');const openSettingsGroups=keepSettingsOpen?new Set([...t.querySelectorAll('details[data-settings-group][open]')].map(d=>d.dataset.settingsGroup)):new Set();lastRenderedPageKey=pageKey;const categoryMenu=$('catmenu');if(categoryMenu&&categoryMenu.parentNode===t)categoryMenu.remove();t.innerHTML='';const categoryRow=document.createElement('div');categoryRow.id='categoryButtons';categoryRow.className='tabs category-button-row';if(categoryMenu)categoryRow.append(categoryMenu);const effectivePins=effectivePinnedCategories();
// Group shortcuts were retired. Keep the empty anchor for older UI callers,
// but do not display it or change stored group preferences.
categoryRow.classList.add('hidden');

let actions=document.createElement('div');actions.className='tab-actions';let undo=document.createElement('button');undo.id='undo';undo.className='iconbtn';undo.title='Undo';undo.setAttribute('aria-label','Undo');undo.innerHTML='<svg viewBox="0 0 24 24"><path d="M9 14 4 9l5-5"/><path d="M4 9h9a6 6 0 0 1 0 12h-2"/></svg>';actions.append(undo);let redo=document.createElement('button');redo.id='redo';redo.className='iconbtn';redo.title='Redo';redo.setAttribute('aria-label','Redo');redo.innerHTML='<svg viewBox="0 0 24 24"><path d="M15 14 20 9l-5-5"/><path d="M20 9h-9a6 6 0 0 0 0 12h2"/></svg>';undo.onclick=()=>{if(!history.length)return;const target=JSON.parse(history.pop());redoHistory.push(captureHistoryCounterpart(target));restoreState(target)};redo.onclick=()=>{if(!redoHistory.length)return;const target=JSON.parse(redoHistory.pop());history.push(captureHistoryCounterpart(target));restoreState(target)};actions.append(redo);let summary=document.createElement('button');summary.id='summary';summary.className='iconbtn view-switch'+(showTop?' active':'');summary.title=showTop?'Switch to Groups view':'Switch to My Rotation view';summary.setAttribute('aria-label',summary.title);summary.setAttribute('aria-pressed',String(showTop));summary.innerHTML=showTop?'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" stroke-linecap="round"/></svg>':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 10.2 12 3l9 7.2V21h-6.5v-7h-5v7H3z" stroke-linejoin="round" stroke-linecap="round"/></svg>';summary.onclick=()=>navigateAfterSettings(()=>{if(showTop)openMasterCategories();else{showTop=true;groceryTabActive=false;allMealsActive=false;editId=null;render()}});actions.insertBefore(summary,actions.firstChild);const search=document.createElement('button');search.id='search';search.className='iconbtn';search.title='Search meals';search.setAttribute('aria-label','Search meals');search.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.7"/><path d="m16 16 5 5" stroke-linecap="round"/></svg>';search.onclick=()=>openMealSearch();if(!showTop)actions.insertBefore(search,summary.nextSibling);

topPanel=document.createElement('div');topPanel.id='topSettingsPanel';topPanel.className='settings-sections';renderTopSettingsPanel=function(){
  topPanel.innerHTML='';
  const weekGroup=makeSettingsGroup('weekdays','Weekday Setup');
  weekGroup.details.classList.toggle('hidden',!showTop);
  topPanel.append(weekGroup.details);
  const hint=document.createElement('div');hint.textContent='Choose one or more groups for each day. Removing a weekday assignment does not delete its group or recipes.';
  hint.className='weekday-setup-hint';weekGroup.content.append(hint);
  orderedDays().forEach(day=>{
    const outer=document.createElement('div');outer.className='weekday-assignment';
    outer.dataset.weekday=day;
    const head=document.createElement('label');head.className='weekday-radio-label';
    const radio=document.createElement('input');radio.type='radio';radio.name='firstWeekday';
    radio.title='Start weekly plan on '+day;radio.setAttribute('aria-label','Start weekly plan on '+day);
    radio.checked=startWeekday===day;radio.value=day;
    radio.onchange=async()=>{
      if(startWeekday===day)return;
      // Prompt only if the proposed first day has categories assigned to it.
      // Cancel restores the original weekday; No changes only the weekday;
      // Yes also reorders pinned category buttons for the new weekday sequence.
      let answer=false;
      if(getDayCategories(day).length){
        answer=await appDialog('Rotate pinned groups to match the new weekday order?',null,'yesnocancel');
      }
      if(answer===null){
        // No state was saved; restore the radio choice in the current editor.
        radio.checked=false;
        const original=document.querySelector('#topSettingsPanel input[name="firstWeekday"][value="'+startWeekday+'"]');
        if(original)original.checked=true;
        renderTabs();renderList();
        return;
      }
      snapshot();
      startWeekday=day;
      localStorage.setItem('mealRotationStartWeekdayV1',day);
      if(answer===true)rotatePinnedCategoriesToWeekdayOrder();
      renderTabs();renderList();
    };
    const label=document.createElement('strong');label.textContent=day;
    head.append(radio,label);outer.append(head);
    const assigned=getDayCategories(day);let pendingRow=null;
    const add=document.createElement('button');add.type='button';add.className='iconbtn weekday-add';setIconButton(add,'add','Add group to '+day);
    const refreshAdd=()=>{add.disabled=!assigned.length||assigned.length>=cats.length||!!pendingRow};
    function makeSelect(value,index){
      const row=document.createElement('div');row.className='weekday-group-row'+(index===0?' weekday-group-first':'');
      const sel=document.createElement('select');sel.setAttribute('aria-label',day+' group '+(index+1));
      const empty=document.createElement('option');empty.value='';empty.textContent='Choose group…';sel.append(empty);
      cats.forEach(c=>{const opt=document.createElement('option');opt.value=c;opt.textContent=c;opt.disabled=assigned.some((x,j)=>j!==index&&x===c);sel.append(opt)});
      sel.value=isEmptyDay(day)?'':(value||'');
      sel.onchange=()=>{
        if(sel.value===EMPTY_DAY_ASSIGNMENT){setDayCategories(day,[EMPTY_DAY_ASSIGNMENT]);return;}
        const next=[...assigned];
        if(index<next.length)next[index]=sel.value;
        else if(sel.value)next.push(sel.value);
        setDayCategories(day,next.filter(Boolean));
      };
      row.append(sel);
      if(index>0){
        const remove=document.createElement('button');remove.type='button';remove.className='iconbtn weekday-remove';
        remove.title=value?'Remove '+value+' from '+day:'Cancel adding group to '+day;remove.setAttribute('aria-label',remove.title);
        const scope=remove.title;setIconButton(remove,index<assigned.length?'delete':'cancel',scope);remove.title=index<assigned.length?scope+'. This removes a weekday assignment, not recipes.':scope;remove.style.minWidth=remove.style.minHeight='44px';remove.querySelector('svg').style.width=remove.querySelector('svg').style.height='18px';
        remove.onclick=()=>{if(index<assigned.length)setDayCategories(day,assigned.filter((_,i)=>i!==index));else{row.remove();pendingRow=null;refreshAdd();add.focus({preventScroll:true})}};row.append(remove);
      }
      outer.append(row);return {row,select:sel};
    }
    if(assigned.length)assigned.forEach(makeSelect);else makeSelect('',0);
    add.onclick=()=>{if(add.disabled)return;const next=makeSelect('',assigned.length);pendingRow=next.row;refreshAdd();next.select.focus({preventScroll:true})};
    refreshAdd();outer.append(add);weekGroup.content.append(outer);
  });
}
;let settings=document.createElement('button');settings.id='settings';settings.className='iconbtn';settings.title='Settings and backups';settings.setAttribute('aria-label','Settings and backups');settings.setAttribute('aria-expanded','false');settings.innerHTML='<svg viewBox="0 0 24 24">'+appIconSvg.settings+'</svg>';actions.append(settings);let panel=document.createElement('div');panel.id='settingsPanel';panel.className='settings-panel hidden';const upperSplit=splitPlanSettings();
const displayGroup=makeSettingsGroup('display','Display');populateTimeSettings(displayGroup.content);populateCookedDateSetting(displayGroup.content);populateMakeAheadSetting(displayGroup.content);
 const manualOrderOption=document.createElement('label');manualOrderOption.className='settings-display-option';
 const manualOrderCheck=document.createElement('input');manualOrderCheck.type='checkbox';manualOrderCheck.checked=manualRecipeOrdering;
 manualOrderCheck.onchange=()=>{manualRecipeOrdering=manualOrderCheck.checked;saveManualRecipeOrdering();renderList()};
 manualOrderOption.append(manualOrderCheck,document.createTextNode('Enable manual recipe ordering'));displayGroup.content.append(manualOrderOption);

const sizeWrap=document.createElement('div');sizeWrap.className='meal-text-size-setting';
const sizeLabel=document.createElement('label');sizeLabel.textContent='Text Size';sizeLabel.htmlFor='mealTextSizeSelect';
const sizeSelect=document.createElement('select');sizeSelect.id='mealTextSizeSelect';sizeSelect.setAttribute('aria-label','Text Size');
for(const [value,label] of [['normal','Normal'],['large','Large'],['extra','Extra Large']]){const option=document.createElement('option');option.value=value;option.textContent=label;sizeSelect.append(option)}
sizeSelect.value=mealTextSize;
sizeSelect.onchange=()=>{mealTextSize=sizeSelect.value;localStorage.setItem(mealTextSizeKey,mealTextSize);applyMealTextSize()};
sizeWrap.append(sizeLabel,sizeSelect);displayGroup.content.prepend(sizeWrap);
panel.append(displayGroup.details);
recipeBulkBackupAPI={capture:captureBackupStorage,validate:validateBackupStorage,restore:restoreBackupStorage};
let exportBtn=document.createElement('button');exportBtn.textContent='Export backup';exportBtn.onclick=()=>{persist();saveActiveMealPlan();saveTimeDisplayPrefs();return exportRecipeBackup({version:2,cats,active,meals,weekdayCategories,weekdayMealOverrides,weekdayColors,categoryColors,timeDisplayPrefs,masterOpenMode,masterPinsOverride,autoPinTopCategories,applyPinsToAllTabs,pinnedCats,expandedCats,mealPlans:{plans:mealPlans,activeId:activePlanId},showMealPlanTabs,storage:captureBackupStorage()})};
let restoreBtn=document.createElement('button');restoreBtn.textContent='Restore backup';
restoreBtn.onclick=()=>{
 const input=document.createElement('input');input.type='file';input.accept='.json,application/json,*/*';
 input.onchange=async()=>{
  const file=input.files?.[0];if(!file)return;
  try{
   const d=JSON.parse(await file.text());
   if(d.version>=2){
    const replacement=normalizeImportedBackup(d);validateBackupStorage(replacement);
    const preparation=await prepareOptionalBackupPhotos(d);if(preparation.cancelled)return;
    const photoWarnings=preparation.warnings;
    restoreBackupStorage(replacement,{id:'backup-restore',kind:'backup-restore',ownerId:null,retry:()=>{restoreBackupStorage(replacement);recipePhotoNotice(photoWarnings);mealPersistence.reload()}});
    recipePhotoNotice(photoWarnings);backupRestoreReloadPending=true;location.reload();return;
   }
   validateBackupCore(startupCore(d));
   const legacyPreparation=await prepareOptionalBackupPhotos(d);if(legacyPreparation.cancelled)return;
   const legacyPhotoWarnings=legacyPreparation.warnings;snapshot();
   if(!writeMasterGroupOrder(null,false))throw Error('Group order could not be reset');
   cats=d.cats;meals=d.meals;
   if(d.weekdayCategories&&typeof d.weekdayCategories==='object')weekdayCategories=d.weekdayCategories;
   if(typeof d.autoPinTopCategories==='boolean'){autoPinTopCategories=true;localStorage.setItem('mealRotationAutoPinTopCategoriesV1',String(autoPinTopCategories))}
   if(typeof d.applyPinsToAllTabs==='boolean'){applyPinsToAllTabs=d.applyPinsToAllTabs;localStorage.setItem('mealRotationApplyPinsAllTabsV1',String(applyPinsToAllTabs))}
   if(['all','current','across','none'].includes(d.masterOpenMode))masterOpenMode=d.masterOpenMode;
   if(typeof d.masterPinsOverride==='boolean')masterPinsOverride=d.masterPinsOverride;saveMasterOpeningPrefs();
   if(Array.isArray(d.pinnedCats)){pinnedCats=d.pinnedCats.filter(c=>cats.includes(c));localStorage.setItem('mealRotationPinnedCategoriesV1',JSON.stringify(pinnedCats))}
   if(Array.isArray(d.expandedCats)){expandedCats=d.expandedCats.filter(c=>cats.includes(c));localStorage.setItem('mealRotationExpandedCategoriesV1',JSON.stringify(expandedCats))}
   if(d.weekdayMealOverrides&&typeof d.weekdayMealOverrides==='object')weekdayMealOverrides=d.weekdayMealOverrides;
   if(d.mealPlans)restoreMealPlansFromBackup(d.mealPlans);
   if(typeof d.showMealPlanTabs==='boolean'){showMealPlanTabs=d.showMealPlanTabs;localStorage.setItem('mealRotationShowPlanTabsV1',String(showMealPlanTabs))}
   saveWeekdayCategories();saveWeekdayMealOverrides();
   if(d.categoryColors&&typeof d.categoryColors==='object'&&!Array.isArray(d.categoryColors)){categoryColors=Object.fromEntries(Object.entries(d.categoryColors).filter(([c,color])=>typeof c==='string'&&/^#[0-9a-fA-F]{6}$/.test(color)));saveCategoryColors()}
   weekdayColors=d.weekdayColors&&typeof d.weekdayColors==='object'&&!Array.isArray(d.weekdayColors)?Object.fromEntries(Object.entries(d.weekdayColors).filter(([day,color])=>weekdays.includes(day)&&/^#[0-9a-fA-F]{6}$/.test(color))):deriveWeekdayColors(categoryColors);saveWeekdayColors();
   if(d.timeDisplayPrefs){setTimeDisplayPrefs(d.timeDisplayPrefs);saveTimeDisplayPrefs()}
   active=cats.includes(d.active)?d.active:(cats[0]||'Soup');id=Math.max(0,...meals.map(m=>Number(m.id)||0))+1;editId=null;menuCat=null;
   localStorage.removeItem(COOKING_SESSIONS_KEY);cookingSessions={version:1,occurrences:{}};cookingStorageInvalid=false;
   localStorage.removeItem(OCCURRENCE_SCALES_KEY);occurrenceScales={version:1,occurrences:{}};scaleStorageInvalid=false;
   persist();render();panel.classList.add('hidden');settings.setAttribute('aria-expanded','false');if(legacyPhotoWarnings.length)showAppMessage(legacyPhotoWarnings.join(' '));
  }catch(e){alert('Backup rejected or restore failed: '+e.message+'. No changes were made if validation failed.')}
 };input.click();
};
let closeSettings=document.createElement('button');closeSettings.textContent='Close';closeSettings.onclick=async()=>{await finishSettings('ask');render()};let importBtn=document.createElement('button');importBtn.textContent='Import recipes';importBtn.title='Import recipe files or Trello boards into Ideas';importBtn.onclick=()=>openRecipeImportSourcePicker();const planGroup=displayGroup;
 const planOption=document.createElement('label');planOption.className='settings-display-option settings-display-option-with-help';
 const planCheck=document.createElement('input');planCheck.type='checkbox';planCheck.checked=showMealPlanTabs;
 planCheck.onchange=()=>{showMealPlanTabs=planCheck.checked;localStorage.setItem('mealRotationShowPlanTabsV1',String(showMealPlanTabs));renderList()};
 const planCopy=document.createElement('span');planCopy.className='settings-display-option-copy';
 const planLabel=document.createElement('span');planLabel.id='mealPlanTabsLabel';planLabel.textContent='Tabs';
 const planHint=document.createElement('small');planHint.id='mealPlanTabsHint';planHint.className='settings-display-option-help';planHint.textContent='Hide tabs to focus on your currently selected meal plan. Other plans are preserved.';
 planCheck.setAttribute('aria-labelledby',planLabel.id);planCheck.setAttribute('aria-describedby',planHint.id);
 planCopy.append(planLabel,planHint);planOption.append(planCheck,planCopy);planGroup.content.append(planOption);
 const addPlan=document.createElement('button');addPlan.type='button';addPlan.className='smallbtn';addPlan.textContent='Add Meal Tab';addPlan.style.minHeight='44px';addPlan.onclick=()=>navigateAfterSettings(openAddMealTabDialog);planGroup.content.append(addPlan);
 const backupGroup=makeSettingsGroup('backups','Data & Backups');const backupRow=document.createElement('div');backupRow.className='settings-backup-controls';backupRow.append(exportBtn,importBtn,restoreBtn);backupGroup.content.append(backupRow,buildRecipeSageRefresh({capture:captureBackupStorage,validate:validateBackupStorage,database:'meal-rotation-recipesage-safety'}));panel.append(backupGroup.details);
 panel.append(makeSettingsFooter());
 const help=document.createElement('button');help.id='help';help.className='iconbtn';help.title='Help and gestures';help.setAttribute('aria-label','Help and gestures');help.innerHTML='<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9.6 9a2.5 2.5 0 1 1 4.2 1.8c-1.1 1-1.8 1.3-1.8 2.7M12 17h.01" stroke-linecap="round"/></svg>';help.onclick=()=>openHelpModal();actions.append(help);settings.onclick=async()=>{
 const opening=panel.classList.contains('hidden');
 if(!opening){await finishSettings('ask');render();return}
 if(settingsBaseline!==null&&activeSettingsPanel==='lower'){
  await finishSettings('ask');render();document.getElementById('settings')?.click();return;
 }
 if(settingsBaseline===null)settingsBaseline=captureSettingsDraft();
 activeSettingsPanel='upper';
 renderTopSettingsPanel();panel.insertBefore(topPanel,displayGroup.details);
 panel.classList.remove('hidden');settings.classList.add('active');settings.setAttribute('aria-expanded','true');
 };t.append(actions,panel,categoryRow);if(menuCat&&cats.includes(menuCat)){const menu=$('catmenu');categoryRow.append(menu)}if(splitPlanSettings()&&document.querySelector('#list .meal-plan-tabs'))document.querySelector('#list .meal-plan-tabs').after(categoryRow);if(keepSettingsOpen){settings.click();t.querySelectorAll('details[data-settings-group]').forEach(d=>{d.open=openSettingsGroups.has(d.dataset.settingsGroup)})}}// Capture the category before opening a dialog: a click on the dialog is outside
// the category toolbar and will clear menuCat via the document pointer handler.
function openCategoryDeleteDialog(category){
 if(!category||!cats.includes(category))return;
 const count=meals.filter(m=>m.cat===category).length;
 const overlay=document.createElement('div');
 overlay.id='categoryDeleteDialog';
 overlay.style.cssText='position:fixed;inset:0;z-index:16000;background:#0008;display:flex;align-items:center;justify-content:center;padding:16px';
 const panel=document.createElement('div');
 panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-labelledby','categoryDeleteHeading');
 panel.style.cssText='width:100%;max-width:480px;max-height:90vh;overflow-y:auto;background:#fff;color:#242424;border-radius:16px;padding:20px;box-shadow:0 12px 36px #0003';
 const heading=document.createElement('div');heading.id='categoryDeleteHeading';heading.textContent='Delete “'+category+'” group?';heading.style.cssText='font-size:19px;font-weight:600;margin-bottom:10px';
 const explanation=document.createElement('p');explanation.textContent=count+' '+(count===1?'recipe':'recipes')+' in this group. Choose Keep recipes to move them before removing this group. Deleting the group and its recipes deletes recipes that exist only here; shared recipes remain in their other groups. Unrelated groups are not deleted.';explanation.style.cssText='font-size:14px;line-height:1.4;color:#666;margin:0 0 16px';
 const actions=document.createElement('div');actions.style.cssText='display:flex;flex-direction:column;gap:10px';
 const deleteButton=document.createElement('button');deleteButton.type='button';deleteButton.className='smallbtn';setIconButton(deleteButton,'delete','Delete group and its recipes');deleteButton.append(document.createTextNode('Delete group and its recipes'));deleteButton.querySelector('svg').style.width=deleteButton.querySelector('svg').style.height='18px';deleteButton.style.cssText='display:flex;gap:8px;align-items:center;justify-content:center;min-height:44px;width:100%;padding:12px;text-align:center;font-size:16px';
 const moveLabel=document.createElement('label');moveLabel.textContent='Move recipes to:';moveLabel.style.cssText='font-size:14px;margin-top:7px';
 const destination=document.createElement('select');destination.setAttribute('aria-label','Move recipes to group');destination.style.cssText='width:100%;min-height:44px;padding:9px;border:1px solid #ccc;border-radius:9px;background:#fff;color:#242424';
 const options=cats.filter(c=>c!==category);
 options.forEach(c=>{const opt=document.createElement('option');opt.value=c;opt.textContent=c;destination.append(opt)});
 const newOption=document.createElement('option');newOption.value='__create_new_category__';newOption.textContent='Create new group…';destination.append(newOption);
 if(!options.length)destination.value=newOption.value;
 const newName=document.createElement('input');newName.type='text';newName.setAttribute('aria-label','New group name');newName.placeholder='New group name';newName.style.cssText='display:none;width:100%;min-height:44px;padding:9px;border:1px solid #ccc;border-radius:9px;background:#fff;color:#242424';
 const moveButton=document.createElement('button');moveButton.type='button';moveButton.className='smallbtn';
 setIconButton(moveButton,'save','Confirm moving recipes and deleting group');
 const cancel=document.createElement('button');cancel.type='button';cancel.className='smallbtn';
 setIconButton(cancel,'cancel','Cancel group deletion');
 const iconActions=document.createElement('div');
 iconActions.className='category-delete-actions';iconActions.style.cssText='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;align-items:center;justify-content:stretch;margin-top:4px;width:100%';
 iconActions.append(moveButton,cancel);
 const keepButton=document.createElement('button');keepButton.type='button';keepButton.className='smallbtn';
 keepButton.textContent='Delete group, but keep recipes';
 keepButton.style.cssText='width:100%;padding:12px;text-align:center;font-size:16px';
 const moveControls=document.createElement('div');moveControls.className='hidden';
 moveControls.style.cssText='display:flex;flex-direction:column;gap:10px';
 keepButton.onclick=()=>{deleteButton.classList.add('hidden');keepButton.classList.add('hidden');initialCancel.classList.add('hidden');moveControls.classList.remove('hidden');destination.focus()};
 const error=document.createElement('div');error.setAttribute('role','alert');error.style.cssText='display:none;font-size:13px;color:#a33';
 function syncNew(){newName.style.display=destination.value===newOption.value?'block':'none';error.style.display='none'}
 destination.onchange=syncNew;syncNew();
 function finish(kind,target){
  if(!cats.includes(category)){overlay.remove();return}
  if(kind==='move'){
   if(target===newOption.value){target=newName.value.trim();if(!target){error.textContent='Enter a name for the new group.';error.style.display='block';newName.focus();return}}
   const existing=cats.find(c=>c.toLowerCase()===target.toLowerCase());
   if(existing)target=existing;
   if(target===category){error.textContent='Choose a different group.';error.style.display='block';return}
  }
  try{removeMealCategory(category,kind,target)}catch(e){error.textContent='Could not update group. No changes saved.';error.style.display='block';return}
  overlay.remove();
 }
 deleteButton.onclick=()=>finish('delete',null);
 moveButton.onclick=()=>finish('move',destination.value);
 cancel.onclick=()=>overlay.remove();
 overlay.onclick=e=>{if(e.target===overlay)overlay.remove()};
 moveControls.append(moveLabel,destination,newName,error,iconActions);
 const initialCancel=document.createElement('button');initialCancel.type='button';initialCancel.className='smallbtn';setIconButton(initialCancel,'cancel','Cancel group deletion');initialCancel.onclick=()=>overlay.remove();
 actions.append(keepButton,deleteButton,moveControls,initialCancel);
 initialCancel.style.cssText='align-self:center;border:0;background:transparent;min-width:60px;min-height:44px;margin-top:2px';
 cancel.style.cssText='border:0;background:transparent;min-width:60px;min-height:44px';
 panel.append(heading,explanation,actions);overlay.append(panel);document.body.append(overlay);
 keepButton.focus({preventScroll:true});overlay.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();overlay.remove()}if(e.key==='Tab'){const controls=[...panel.querySelectorAll('button,input,select')].filter(el=>el.getClientRects().length&&!el.disabled),first=controls[0],last=controls.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}};
}
function removeMealCategory(category,action,target){
 if(!cats.includes(category)||!['delete','move'].includes(action))return;
 if(action==='move'&&(!target||target===category))throw Error('Invalid destination group');
 if(recipeBulkBusy)throw Error('Another recipe update is in progress.');
 if(groceryCheckStorageInvalid||cookingStorageInvalid||scaleStorageInvalid)throw Error('Saved progress could not be read. Export a backup before changing groups.');
 const stored=recipeBulkBackupAPI.capture();recipeBulkBackupAPI.validate(stored);
 const before=JSON.parse(captureState()),raw=JSON.parse(JSON.stringify({sessions:cookingSessions,scales:occurrenceScales})),selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');
 const memory={cats,active,meals,masterGroupOrder,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters,pinnedCats,expandedCats,topCounts,categoryColors,weekdayColors,mealPlans,editId,menuCat,cookingSessions,occurrenceScales,groceryOccurrenceChecks,previouslyActiveLinkedIds,cookingScheduleSignature,recipeStates:new Map(cookingRecipeStates)};
 recipeBulkBusy=true;
 try{
  bulkRecipeStorageDraft=new Map(Array.from({length:mealBulkStorageBase.length},(_,i)=>{const key=mealBulkStorageBase.key(i);return [key,mealBulkStorageBase.getItem(key)]}));
  ({cats,active,meals,masterGroupOrder,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters,pinnedCats,expandedCats,topCounts,categoryColors,weekdayColors,mealPlans}=JSON.parse(JSON.stringify(before)));
  cookingSessions=JSON.parse(JSON.stringify(raw.sessions));occurrenceScales=JSON.parse(JSON.stringify(raw.scales));groceryOccurrenceChecks=JSON.parse(JSON.stringify(before.groceryOccurrenceChecks));previouslyActiveLinkedIds=new Set(previouslyActiveLinkedIds);
  const groceryBefore=captureGroceryCheckStates();removeMealCategoryMutation(category,action,target);
  before.groupUndoGrocery=captureGroupGroceryUndo(groceryBefore,before);
  // Reuse dependency-aware occurrence restoration: recover removed or changed
  // contexts and remove contexts created by the group operation on Undo.
  const keys=new Set();for(const [prior,current]of [[raw.sessions.occurrences,cookingSessions.occurrences],[raw.scales.occurrences,occurrenceScales.occurrences]])for(const key of new Set([...Object.keys(prior),...Object.keys(current)]))if(JSON.stringify(prior[key])!==JSON.stringify(current[key]))keys.add(key);
  before.skippedCookingState={keys:[...keys],sessions:raw.sessions.occurrences,scales:raw.scales.occurrences};
  const nextSelections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');before.groupUndoIngredientSelections={};for(const key of new Set([...Object.keys(selections),...Object.keys(nextSelections)]))if(JSON.stringify(selections[key])!==JSON.stringify(nextSelections[key]))before.groupUndoIngredientSelections[key]=Object.hasOwn(selections,key)?selections[key]:null;
  const proposed=recipeBulkBackupAPI.capture();recipeBulkBackupAPI.validate(proposed);bulkRecipeStorageDraft=null;
  recipeBulkBackupAPI.restore(proposed,{id:'group:'+JSON.stringify([category,action,target]),kind:'group-removal',ownerId:null,retry:()=>removeMealCategory(category,action,target)});
  snapshot(JSON.stringify(before));
 }catch(error){
  bulkRecipeStorageDraft=null;({cats,active,meals,masterGroupOrder,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters,pinnedCats,expandedCats,topCounts,categoryColors,weekdayColors,mealPlans,editId,menuCat,cookingSessions,occurrenceScales,groceryOccurrenceChecks,previouslyActiveLinkedIds,cookingScheduleSignature}=memory);cookingRecipeStates.clear();for(const [key,value]of memory.recipeStates)cookingRecipeStates.set(key,value);throw error;
 }finally{bulkRecipeStorageDraft=null;recipeBulkBusy=false}
 render();document.getElementById('categoryDeleteDialog')?.remove();
}
function removeMealCategoryMutation(category,action,target){
 if(!cats.includes(category)||!['delete','move'].includes(action))return;
 const move=action==='move';
 if(move&&(!target||target===category))throw new Error('Invalid destination group');
 if(!removeMasterGroupOrder(category))throw Error('Group order could not be saved');
 const wasPinned=pinnedCats.includes(category),wasExpanded=expandedCats.includes(category);
 if(move){
  if(!cats.includes(target))cats.push(target);
  // A recipe can already be linked to the destination category. Reuse that
  // entry rather than making a duplicate and preserve its grocery selections.
  const existingByIdentity=new Map();
  for(const meal of meals.filter(m=>m.cat===target)){
   const identity=meal.importSourceId?'source:'+meal.importSourceId:meal.linkGroup?'group:'+meal.linkGroup:null;
   if(identity&&!existingByIdentity.has(identity))existingByIdentity.set(identity,meal);
  }
  const redundantIds=new Set();
  let selected=null;
  try{const value=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');if(value&&typeof value==='object'&&!Array.isArray(value))selected=value}catch(e){}
  for(const meal of meals.filter(m=>m.cat===category)){
   const identity=meal.importSourceId?'source:'+meal.importSourceId:meal.linkGroup?'group:'+meal.linkGroup:null;
   const duplicate=identity?existingByIdentity.get(identity):null;
   if(duplicate){
    redundantIds.add(meal.id);
    if(selected&&Array.isArray(selected[String(meal.id)])){
     const oldSelection=Array.isArray(selected[String(duplicate.id)])?selected[String(duplicate.id)]:[];
     selected[String(duplicate.id)]=[...new Set([...oldSelection,...selected[String(meal.id)]])];
    }
   }else{
    meal.cat=target;
    if(identity)existingByIdentity.set(identity,meal);
   }
  }
  if(redundantIds.size)meals=meals.filter(m=>!redundantIds.has(m.id));
  if(selected)try{localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected))}catch(e){}
 }else{
  // This removes category memberships. Other linked category entries survive.
  meals=meals.filter(m=>m.cat!==category);
 }
 removeGroupIdentity(category);cats=cats.filter(c=>c!==category);
 // Entries with only one remaining category no longer need a link group.
 const groupCounts=new Map();
 for(const m of meals)if(m.linkGroup)groupCounts.set(m.linkGroup,(groupCounts.get(m.linkGroup)||0)+1);
 for(const m of meals)if(m.linkGroup&&groupCounts.get(m.linkGroup)===1)m.linkGroup='';
 for(const day of weekdays){
  const original=(Array.isArray(weekdayCategories[day])?weekdayCategories[day]:[weekdayCategories[day]]).filter(Boolean);
  if(!original.includes(category))continue;
  weekdayCategories[day]=[...new Set(original.flatMap(c=>c===category?(move?[target]:[]):[c]))];
  clearWeekdayOverride(day,category);
  if(original[0]===category)delete weekdayMealOverrides[day];
}

 saveWeekdayCategories();saveWeekdayMealOverrides();updateOtherMealPlansForCategory(category,move?target:null);
 pinnedCats=pinnedCats.filter(c=>c!==category);
 expandedCats=expandedCats.filter(c=>c!==category);
 if(move&&!pinnedCats.includes(target)&&!expandedCats.includes(target)){
  (wasPinned?pinnedCats:expandedCats).push(target);
 }
 try{localStorage.setItem('mealRotationPinnedCategoriesV1',JSON.stringify(pinnedCats));localStorage.setItem('mealRotationExpandedCategoriesV1',JSON.stringify(expandedCats))}catch(e){}
 delete topCounts[category];saveTopCounts();
 delete categoryColors[category];saveCategoryColors();
 if(active===category||!cats.includes(active))active=move?target:(cats[0]||'');
 editId=null;menuCat=null;
 persist();
}
function renameCategoryDirect(categoryToRename){
  if(!cats.includes(categoryToRename))return;
  (async()=>{let n=await appDialog('Rename group',categoryToRename,'prompt');if(n&&n.trim()&&cats.includes(categoryToRename)&&!cats.includes(n.trim())){snapshot();let old=categoryToRename;if(!renameMasterGroupOrder(old,n.trim()))return;renameGroupIdentity(old,n.trim());renameDependentGroupState(old,n.trim());cats[cats.indexOf(old)]=n.trim();if(categoryColors[old]){categoryColors[n.trim()]=categoryColors[old];delete categoryColors[old];saveCategoryColors()}meals.forEach(m=>{if(m.cat===old)m.cat=n.trim()});pinnedCats=pinnedCats.map(c=>c===old?n.trim():c);expandedCats=expandedCats.map(c=>c===old?n.trim():c);mealPlans.forEach(p=>{if(Array.isArray(p.pinnedDisplayOrder))p.pinnedDisplayOrder=p.pinnedDisplayOrder.map(c=>c===old?n.trim():c)});try{localStorage.setItem('mealRotationPinnedCategoriesV1',JSON.stringify(pinnedCats));localStorage.setItem('mealRotationExpandedCategoriesV1',JSON.stringify(expandedCats))}catch(e){}weekdays.forEach(day=>{weekdayCategories[day]=(Array.isArray(weekdayCategories[day])?weekdayCategories[day]:[weekdayCategories[day]]).filter(Boolean).map(c=>c===old?n.trim():c);if(weekdayMealOverrides[weekdaySlotKey(day,old)]!==undefined){weekdayMealOverrides[weekdaySlotKey(day,n.trim())]=weekdayMealOverrides[weekdaySlotKey(day,old)];delete weekdayMealOverrides[weekdaySlotKey(day,old)]}});saveWeekdayMealOverrides();saveWeekdayCategories();updateOtherMealPlansForCategory(old,n.trim());active=n.trim();menuCat=n.trim();copyMasterSectionExpansion(old,n.trim());if(masterExpandedCategories.delete(old))masterExpandedCategories.add(n.trim());render()}
  })();
}
function renderMenu(){let box=$('catmenu');if(!box)return;box.innerHTML='';if(!showTop||!menuCat||!cats.includes(menuCat)){box.classList.add('hidden');return}box.classList.remove('hidden');const categoryRow=document.getElementById('categoryButtons');if(categoryRow)categoryRow.append(box);function arrow(direction,label){let b=document.createElement('button');b.className='arrow iconbtn';b.title=label;b.setAttribute('aria-label',label);b.innerHTML=direction<0?'<svg viewBox="0 0 24 24"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>':'<svg viewBox="0 0 24 24"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>';b.onclick=()=>{
  const ordered=getCategoryButtonOrder();
  const i=ordered.indexOf(menuCat),j=i+direction;
  if(j<0||j>=ordered.length)return;
  snapshot();
  if(showTop&&Array.isArray(mealPlans.find(p=>p.id===activePlanId)?.pinnedDisplayOrder)){
    [ordered[i],ordered[j]]=[ordered[j],ordered[i]];
    mealPlans.find(p=>p.id===activePlanId).pinnedDisplayOrder=ordered;
    saveActiveMealPlan();
  }else{
    const a=cats.indexOf(menuCat),b=a+direction;
    if(b<0||b>=cats.length)return;
    [cats[a],cats[b]]=[cats[b],cats[a]];
  }
  renderTabs();renderMenu();
 };box.append(b)}arrow(-1,'Move group left');arrow(1,'Move group right');[['Rename',()=>renameCategoryDirect(menuCat)],['Delete',()=>{const selectedCategory=menuCat;openCategoryDeleteDialog(selectedCategory)}],['Cancel',()=>{menuCat=null;renderMenu()}]].forEach(([txt,fn])=>{let b=document.createElement('button');b.className='smallbtn';setIconButton(b,txt==='Rename'?'rename':txt==='Delete'?'delete':'cancel',txt);b.onclick=fn;box.append(b)})}function bindRenameLongPress(name,m){
  let timer=null,ingredientHeld=false,pressActive=false;
  const stopTimer=()=>{clearTimeout(timer);timer=null};
  name.addEventListener('pointerdown',e=>{
    if(e.pointerType==='mouse'&&e.button!==0)return;
    stopTimer();pressActive=true;ingredientHeld=false;
    // Recognize the long press, but don't create the popup beneath a finger
    // that is still pressed. That could start a second ingredient-row gesture.
    timer=setTimeout(()=>{if(pressActive)ingredientHeld=true},550);
  });
  name.addEventListener('pointerup',e=>{
    stopTimer();
    const shouldOpen=pressActive&&ingredientHeld;
    pressActive=false;
    if(shouldOpen){e.preventDefault();openTopIngredientChooser(m)}
  });
  ['pointerleave','pointercancel'].forEach(ev=>name.addEventListener(ev,()=>{stopTimer();pressActive=false}));
  name.addEventListener('click',e=>{
    if(ingredientHeld){e.preventDefault();e.stopImmediatePropagation();ingredientHeld=false}
  },true);
  name.oncontextmenu=e=>e.preventDefault();
}
function ingredientKey(line){return String(line??'').normalize('NFKC').trim().replace(/\s+/g,' ').toLowerCase()}
// A single whole-week allocation is used by every group and meal-plan tab.
// Keep manual choices and established automatic slots before filling new openings.
function recipeLastCookedTime(meal){
 const time=meal?.lastCooked?new Date(meal.lastCooked).getTime():NaN;
 if(!Number.isFinite(time))return null;const day=new Date(time);day.setHours(0,0,0,0);return day.getTime();
}
// Recipe favorites share one deterministic weighted selector with normal cycling.
// Rendering only reads credits. Explicit outgoing occurrences advance them.
function favoriteRotationPool(category,labels,library,plan){
 const pool=library.filter(m=>m.rotation&&m.cat===category&&recipeMatchesFilters(m,labels));
 if(!plan||pool.length<2||!pool.some(m=>m.favorite===true))return null;
 const key=JSON.stringify([category,[]]),signature=JSON.stringify(pool.map(m=>[String(m.id),m.favorite===true?2:1]).sort((a,b)=>a[0].localeCompare(b[0])));
 const stored=plan.favoriteRotationScores?.[key],scores=stored?.signature===signature&&stored.scores&&typeof stored.scores==='object'?stored.scores:{};
 return {pool,key,signature,scores};
}
function advanceFavoriteRotation(plan,category,outgoing,labels=[],library=meals){
 const state=favoriteRotationPool(category,labels,library,plan);if(!state||!state.pool.some(m=>String(m.id)===String(outgoing.id)))return;
 const scores={},total=state.pool.reduce((sum,m)=>sum+(m.favorite===true?2:1),0);
 for(const m of state.pool){const id=String(m.id),prior=Number.isFinite(state.scores[id])?state.scores[id]:0;scores[id]=prior+(m.favorite===true?2:1)-(id===String(outgoing.id)?total:0)}
 plan.favoriteRotationScores={...(plan.favoriteRotationScores||{}),[state.key]:{signature:state.signature,scores}};return state.signature;
}
function restoreFavoriteRotationTurns(previous,desired){
 for(const turn of previous.favoriteRotationTurns||[]){if(!desired.some(item=>item.planId===turn.planId&&item.day===turn.day&&item.cat===(turn.slotCat||turn.cat)))continue;const plan=mealPlans.find(p=>p.id===turn.planId),state=favoriteRotationPool(turn.cat,[],meals,plan);if(!state||state.signature!==turn.signature)continue;const scores={},total=state.pool.reduce((sum,m)=>sum+(m.favorite===true?2:1),0);for(const m of state.pool){const id=String(m.id),prior=Number.isFinite(state.scores[id])?state.scores[id]:0;scores[id]=prior-(m.favorite===true?2:1)+(id===turn.mealId?total:0)}plan.favoriteRotationScores={...(plan.favoriteRotationScores||{}),[state.key]:{signature:state.signature,scores}}}
}
function refreshFavoriteButtons(){for(const b of document.querySelectorAll('[data-recipe-favorite]')){const meal=meals.find(m=>String(m.id)===b.dataset.recipeFavorite);if(!meal)continue;b.setAttribute('aria-pressed',String(meal.favorite===true));const label=(meal.favorite===true?'Remove from favorites: ':'Add to favorites: ')+(meal.name||'Recipe');b.setAttribute('aria-label',label);b.title=label}}
function toggleRecipeFavorite(meal){
 snapshot();preserveOtherMealPlanChoices(null,null);assignSharedRecipeFields(meal,{favorite:meal.favorite===true?undefined:true});
 persist();renderList();refreshFavoriteButtons();if(recipeViewer)recipeViewer.contentChanged=true;
}
function recipeFavoriteButton(meal){
 const b=document.createElement('button');b.type='button';b.className='recipe-personal-icon recipe-favorite-toggle';b.dataset.recipeFavorite=String(meal.id);b.setAttribute('aria-pressed',String(meal.favorite===true));setRecipeToolbarIcon(b,'heart',(meal.favorite===true?'Remove from favorites: ':'Add to favorites: ')+(meal.name||'Recipe'));
 b.onclick=e=>{e.preventDefault();e.stopPropagation();const current=meals.find(m=>String(m.id)===String(meal.id));if(current)toggleRecipeFavorite(current)};
 for(const event of ['pointerdown','pointerup','touchstart','touchend','dblclick'])b.addEventListener(event,e=>e.stopPropagation());return b;
}
function bindRecipePersonalName(name,meal,showFavorite=true){
 const target=name.parentElement?.classList.contains('recipe-name-with-timer')?name.parentElement:name;
 const wrap=document.createElement('span');wrap.className='recipe-personal-name';target.replaceWith(wrap);wrap.append(target);if(showFavorite&&meal.favorite===true)wrap.append(recipeFavoriteButton(meal));
}

function automaticRecipeCandidates(category,labels=[],library=meals,plan=null){
 const ordered=library.filter(meal=>meal.rotation&&meal.cat===category&&recipeMatchesFilters(meal,labels)).sort((a,b)=>{
  const x=recipeLastCookedTime(a),y=recipeLastCookedTime(b);return x===null?(y===null?0:-1):y===null?1:x-y;
 });
 const weighted=favoriteRotationPool(category,labels,library,plan);if(!weighted)return ordered;
 const credit=m=>(Number.isFinite(weighted.scores[String(m.id)])?weighted.scores[String(m.id)]:0)+(m.favorite===true?2:1);
 return ordered.sort((a,b)=>credit(b)-credit(a));
}
function allocateScheduledWeek(library,categories,plans,days,reservedPlanId=null,reservedByGroup=null){
 const slots=[],occasional=[],used=new Set(),result=new Map(plans.map(plan=>[String(plan.id),[]]));
 for(const plan of plans)for(const day of days){
  const raw=plan.weekdayCategories?.[day],groups=[...new Set((Array.isArray(raw)?raw:[raw]).filter(cat=>categories.includes(cat)))];
  const once=library.find(meal=>String(meal.id)===String(plan.occasionalMeals?.[day]));
  if(once){occasional.push({plan,day,cat:once.cat,meal:once,occasional:true});used.add(String(once.id))}
  for(const cat of groups){
   const key=weekdaySlotKey(day,cat),choice=plan.cycleSlotChoices?.[key];if(choice?.empty===true)continue;
   const chosen=plan.weekdayMealOverrides?.[key]??(groups[0]===cat?plan.weekdayMealOverrides?.[day]:undefined);
   const manual=manualWeekdayMealChoice(plan,day,cat),possible=automaticRecipeCandidates(cat,plan.weekdayRecipeFilters?.[key]||[],library,plan).filter(m=>!choice?.skipReplacement||!(choice.excludedMealIds||[]).includes(String(m.id)));
   const dependent=!!pairedMainGroup(plan,day,cat),preferred=(manual||dependent?library:possible).find(meal=>String(meal.id)===String(chosen)&&(manual||meal.rotation||choice?.parentId));
   slots.push({plan,day,cat,key,choice,possible,preferred,dependent,manual:manual&&!!preferred,meal:null});
  }
 }
 const pendingSides=slots.filter(slot=>slot.dependent&&!slot.manual);for(const slot of pendingSides)slots.splice(slots.indexOf(slot),1);
 // Deliberate manual duplicates stay exact. Their IDs reserve ordinary automatic slots.
 for(const slot of slots.filter(slot=>slot.manual)){slot.meal=slot.preferred;used.add(String(slot.meal.id))}
 const fixed=new Set(used),owners=new Map(),dependentReservations=new Set(pendingSides.filter(slot=>slot.preferred).map(slot=>sharedRecipeIdentity(slot.preferred)));for(const slot of pendingSides)if(slot.preferred){fixed.add(String(slot.preferred.id));used.add(String(slot.preferred.id))}
 for(const slot of slots)if(!slot.manual&&slot.preferred&&slot.choice?.retain&&fixed.has(String(slot.preferred.id)))slot.meal=slot.preferred;
 for(const slot of slots.filter(slot=>!slot.meal&&slot.preferred).sort((a,b)=>(a.choice?.skipReplacement===true)-(b.choice?.skipReplacement===true)))if(!used.has(String(slot.preferred.id))){slot.meal=slot.preferred;used.add(String(slot.meal.id));owners.set(String(slot.meal.id),slot)}
 function place(slot,seenSlots=new Set(),seenIds=new Set()){
  if(seenSlots.has(slot))return false;seenSlots.add(slot);
  const reserved=String(slot.plan.id)===String(reservedPlanId)?reservedByGroup?.get(slot.cat):null;
  const avoid=String(slot.choice?.avoidMealId??''),options=slot.possible.filter(meal=>!fixed.has(String(meal.id))&&!reserved?.has(String(meal.id))&&!seenIds.has(String(meal.id)));
  options.sort((a,b)=>(String(a.id)===avoid)-(String(b.id)===avoid));
  // Try unused choices before moving an established automatic meal. An augmenting
  // path handles overlapping label filters without disturbing manual/retained slots.
  for(const meal of [...options.filter(meal=>!owners.has(String(meal.id))),...options.filter(meal=>owners.has(String(meal.id)))]){
   const id=String(meal.id),owner=owners.get(id);if(owner===slot)continue;
   const ownerReserved=owner&&String(owner.plan.id)===String(reservedPlanId)?reservedByGroup?.get(owner.cat):null;
   if(owner&&(owner.choice?.retain||owner.choice?.parentId||ownerReserved?.has(id)||!place(owner,new Set(seenSlots),new Set([...seenIds,id]))))continue;
   if(slot.meal&&owners.get(String(slot.meal.id))===slot){owners.delete(String(slot.meal.id));used.delete(String(slot.meal.id))}
   slot.meal=meal;owners.set(id,slot);used.add(id);return true;
  }
  return false;
 }
 for(const slot of slots.filter(slot=>!slot.meal))place(slot);
 // Repeats are a bounded fallback only after all distinct assignments were tried.
 for(const slot of slots.filter(slot=>!slot.meal))slot.meal=slot.possible.find(meal=>String(meal.id)!==String(slot.choice?.avoidMealId??''))||slot.possible[0];
 // Main slots are resolved before compatible side openings; side allocation cannot reassign a main.
 for(const slot of slots)if(slot.meal)fixed.add(String(slot.meal.id));
 for(const slot of pendingSides){
  const entries=slots.filter(other=>other.plan.id===slot.plan.id&&other.meal).map(other=>({day:other.day,cat:other.cat,meal:other.meal}));
  slot.possible=automaticSlotCandidates(slot.plan,slot.day,slot.cat,library,entries).filter(m=>!slot.choice?.skipReplacement||!(slot.choice.excludedMealIds||[]).includes(String(m.id)));
  if(slot.preferred){slot.meal=slot.preferred;used.add(String(slot.meal.id));fixed.add(String(slot.meal.id))}
  else{const prior=library.find(m=>String(m.id)===String(slot.choice?.avoidMealId)),avoid=prior&&sharedRecipeIdentity(prior),unused=slot.possible.filter(m=>!dependentReservations.has(sharedRecipeIdentity(m))&&!slots.some(other=>other.meal&&sharedRecipeIdentity(other.meal)===sharedRecipeIdentity(m))),distinct=(unused.length?unused:slot.possible).filter(m=>sharedRecipeIdentity(m)!==avoid);if(distinct.length)slot.possible=distinct;else if(unused.length)slot.possible=unused;place(slot);if(!slot.meal)slot.meal=slot.possible[0];}
  slots.push(slot);
 }
 for(const slot of slots)if(slot.meal){
  const parent=String(slot.choice?.mealId)===String(slot.meal.id)?slot.choice?.parentId:'';
  result.get(String(slot.plan.id)).push({day:slot.day,cat:slot.cat,meal:slot.meal,scheduledSlot:true,...(slot.dependent?{dependentSide:true}:{}),...(String(slot.plan.occasionalMeals?.[slot.day])===String(slot.meal.id)?{occasional:true}:{}),...(parent?{linkedTo:parent}:{})});
 }
 for(const item of occasional){const entries=result.get(String(item.plan.id));if(!entries.some(entry=>entry.day===item.day&&String(entry.meal.id)===String(item.meal.id)))entries.push({day:item.day,cat:item.cat,meal:item.meal,occasional:true})}
 for(const entries of result.values())entries.sort((a,b)=>days.indexOf(a.day)-days.indexOf(b.day));return result;
}
// Persist optional choices in the existing plan structure so date edits or view
// changes cannot silently reassign established meals. Never modify the manual queue.
function stabilizeAutomaticWeekSlots(){
 if(restoringRotationCalendars)return false;
 const before=JSON.stringify(mealPlans),schedules=new Map();
 for(const plan of mealPlans){const current=plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan;schedules.set(plan.id,getDisplayedWeekdayMealsForPlan(current,null,null,null,true))}
 for(const plan of mealPlans){
  rememberDependentSideState(plan,schedules.get(plan.id)||[]);plan.weekdayMealOverrides={...(plan.weekdayMealOverrides||{})};plan.cycleRetainedSlots={...(plan.cycleRetainedSlots||{})};plan.cycleSlotChoices={...(plan.cycleSlotChoices||{})};
  for(const item of schedules.get(plan.id)||[]){
   if(!rotationSelectable(item,plan))continue;const key=weekdaySlotKey(item.day,item.cat),id=String(item.meal.id),old=plan.cycleSlotChoices[key],manual=manualWeekdayMealChoice(plan,item.day,item.cat,id);
   plan.weekdayMealOverrides[key]=id;plan.cycleRetainedSlots[key]=id;
   plan.cycleSlotChoices[key]={...(old&&String(old.mealId)===id?old:{}),...(manual?{substitution:true}:{}),mealId:id,parentId:String(item.linkedTo??'')};
  }
 }
 weekdayMealOverrides={...(mealPlans.find(plan=>plan.id===activePlanId)?.weekdayMealOverrides||{})};return before!==JSON.stringify(mealPlans);
}
// Current-week presentation is separate from the permanent recipe queues.
// Optional plan fields travel through existing snapshots, backups and recovery.
function weekSchedule(plan){return plan.weekSchedule||{version:1,slots:{},order:{}}}
function editableWeekSchedule(plan){return plan.weekSchedule||(plan.weekSchedule={version:1,slots:{},order:{}})}
function temporarySlotKey(day,cat){return weekdaySlotKey(day,cat||'@day')}
function scheduleDisplayKey(entry){return JSON.stringify([entry.cat,...(entry.occasional?['occasional',String(entry.meal?.id??'')]:[])])}
function weekDisplayRank(plan,entry,base){
 const order=weekSchedule(plan).order[entry.day]||[],token=entry.meal?scheduleDisplayKey(entry):null;
 // Assigned groups are stable display slots, independent of recipe IDs, empties,
 // occasional/one-time presentation, or the number of meals the planner emits.
 const raw=plan.weekdayCategories?.[entry.day],groups=(Array.isArray(raw)?raw:[raw]).filter(cat=>typeof cat==='string');
 if(groups.includes(entry.cat)){
  const arranged=[];for(const key of order){try{const cat=JSON.parse(key)[0];if(groups.includes(cat)&&!arranged.includes(cat))arranged.push(cat)}catch(e){}}
  for(const cat of groups)if(!arranged.includes(cat))arranged.push(cat);return arranged.indexOf(entry.cat);
 }
 let index=order.indexOf(token);
 const original=base.find(item=>item.day===entry.day&&(item.cat===entry.cat&&(entry.temporary||entry.temporaryEmpty||entry.emptyWeek)||scheduleDisplayKey(item)===token));
 if(index<0&&original&&(entry.temporary||entry.temporaryEmpty||entry.emptyWeek))index=order.indexOf(scheduleDisplayKey(original));
 if(index>=0)return index;const fallback=base.filter(item=>item.day===entry.day).indexOf(original);return order.length+(fallback<0?base.length:fallback);
}
function applyWeekSchedule(plan,entries,days){
 if(!plan.weekSchedule)return entries;
 const state=weekSchedule(plan),hidden=new Set(entries.filter(entry=>state.slots[temporarySlotKey(entry.day,entry.cat)]).map(entry=>entry.day+'|'+String(entry.meal.id)));
 const result=entries.filter(entry=>!state.slots[temporarySlotKey(entry.day,entry.cat)]&&!(entry.linkedTo!=null&&hidden.has(entry.day+'|'+String(entry.linkedTo))&&!rotationGroupScheduled(plan,entry.day,entry.cat))&&!state.slots[temporarySlotKey(entry.day,null)]);
 for(const [key,item] of Object.entries(state.slots))if(item.kind==='once'){
  const split=key.indexOf('::'),day=key.slice(0,split),cat=key.slice(split+2);
  result.push({day,cat,meal:item.meal,scheduleOnly:true,temporary:true});
 }
 for(const parent of result.filter(entry=>entry.meal.temporaryMeal))for(const id of parent.meal.linkedMealIds||[]){
  const side=meals.find(meal=>String(meal.id)===String(id));if(!side||result.some(entry=>entry.day===parent.day&&String(entry.meal.id)===String(id)))continue;
  const cat=linkedRecipePlacement(plan,parent.day,parent,side,result),key=temporarySlotKey(parent.day,cat),choice=plan.cycleSlotChoices?.[weekdaySlotKey(parent.day,cat)];
  if(state.slots[key]||(choice?.blockedParents||[]).some(id=>String(id)===String(parent.meal.id))||(choice?.excludedMealIds||[]).some(id=>String(id)===String(side.id)))continue;
  const prior=result.findIndex(entry=>entry.day===parent.day&&entry.cat===cat);if(prior>=0&&manualWeekdayMealChoice(plan,parent.day,cat,result[prior].meal.id))continue;
  const linked={day:parent.day,cat,meal:side,linkedTo:parent.meal.id,scheduledSlot:rotationGroupScheduled(plan,parent.day,cat)};if(prior>=0)result.splice(prior,1,linked);else result.push(linked);
 }
 return result.sort((a,b)=>{
  if(a.day!==b.day)return days.indexOf(a.day)-days.indexOf(b.day);
  return weekDisplayRank(plan,a,entries)-weekDisplayRank(plan,b,entries);
 });
}
function emptyWeekEntries(plan){
 return Object.entries(weekSchedule(plan).slots).filter(([,item])=>item.kind==='empty').map(([key])=>{
  const split=key.indexOf('::'),day=key.slice(0,split),cat=key.slice(split+2);
  return {day,cat,scheduleOnly:true,emptyWeek:true,meal:{id:'empty:'+plan.id+':'+key,name:'Empty this week'+(cat==='@day'?'':' · '+cat),cat,ingredients:[]}};
 });
}
function queueWeekEntries(plan){return getDisplayedWeekdayMealsForPlan(plan,null,null,null,true)}
function rotationWeekEntries(plan,saved=null){return getDisplayedWeekdayMealsForPlan(plan,null,saved).concat(emptyWeekEntries(plan))}
function rotationSelectionEntries(plan,saved=null){
 const entries=getDisplayedWeekdayMealsForPlan(plan,null,saved).concat(emptyWeekEntries(plan));
 for(const day of weekdays){const raw=plan.weekdayCategories?.[day];for(const cat of Array.isArray(raw)?raw:[raw]){
  if(!cats.includes(cat)||entries.some(item=>item.day===day&&(item.cat===cat||item.cat==='@day')))continue;
  entries.push({day,cat,scheduleOnly:true,emptyWeek:true,emptyAssigned:true,meal:{id:'empty:'+plan.id+':'+weekdaySlotKey(day,cat),name:'—',cat,ingredients:[]}});
 }}return entries;
}
function rotationAdvancesRecipe(item,plan,entries=[]){
 const parent=pairedMainGroup(plan,item.day,item.cat);if(parent&&plan.cycleSlotChoices?.[weekdaySlotKey(item.day,parent)]?.preserveSideQueue===true)return false;
 return !item.scheduleOnly&&!manualWeekdayMealChoice(plan,item.day,item.cat,item.meal.id)&&!entries.some(parent=>parent.day===item.day&&String(parent.meal.id)===String(item.linkedTo)&&(parent.scheduleOnly||parent.meal.temporaryMeal||manualWeekdayMealChoice(plan,parent.day,parent.cat,parent.meal.id)));
}
function clearTemporarySlot(plan,day,cat){if(plan.weekSchedule)delete plan.weekSchedule.slots[temporarySlotKey(day,cat)]}
// Each temporary slot holds only shopping progress for its current cycle.
// Permanent ingredient selections and recipe definitions are never copied here.
function temporaryGroceryOwner(plan,entry,base=queueWeekEntries(plan)){
 const slots=weekSchedule(plan).slots,own=temporarySlotKey(entry.day,entry.cat),day=temporarySlotKey(entry.day,null);
 if(slots[own])return own;if(slots[day])return day;
 if(entry.linkedTo!=null&&!rotationGroupScheduled(plan,entry.day,entry.cat)){
  const parent=base.find(item=>item.day===entry.day&&String(item.meal.id)===String(entry.linkedTo)),key=parent&&temporarySlotKey(parent.day,parent.cat);if(key&&slots[key])return key;
 }
 return null;
}
function hiddenWeekEntries(plan){const base=queueWeekEntries(plan);return base.filter(entry=>temporaryGroceryOwner(plan,entry,base))}
function heldWeekGroceryChecks(plan){
 const checks={};for(const item of Object.values(weekSchedule(plan).slots))Object.assign(checks,item.groceryChecks||{});return checks;
}
function heldWeekGroceryQuantities(plan){const amounts={...weekSchedule(plan).linkedGroceryQuantities};for(const item of Object.values(weekSchedule(plan).slots))Object.assign(amounts,item.groceryQuantities||{});return amounts}
function updateTemporaryGroceryChecks(plan,previousSlots,before){
 const slots=weekSchedule(plan).slots,base=queueWeekEntries(plan),visible=new Set(getGroceryContributions(true).map(source=>source.id));
 for(const [key,item]of Object.entries(slots))if(previousSlots[key]?.groceryChecks){item.groceryChecks={...previousSlots[key].groceryChecks,...item.groceryChecks};item.groceryQuantities={...previousSlots[key].groceryQuantities,...item.groceryQuantities}};
 for(const [id,item]of before){const source=item.source;if(!source||source.planId!==plan.id||visible.has(id))continue;
  const occurrence=JSON.parse(source.occurrence),entry=base.find(entry=>entry.day===source.day&&String(entry.meal.id)===String(source.mealId))||{day:source.day,cat:source.cat,meal:{id:source.mealId},...(occurrence[3].startsWith('linked:')?{linkedTo:occurrence[3].slice(7)}:{})};
  const key=temporaryGroceryOwner(plan,entry,base);if(key){slots[key].groceryChecks={...slots[key].groceryChecks,[id]:item.checked};if(item.amount)slots[key].groceryQuantities={...slots[key].groceryQuantities,[id]:{...item.amount}}}
 }
}

function changeTemporaryWeek(update){
 if(groceryCheckStorageInvalid||mealPersistence.paused){showAppMessage('Saved data is unavailable. No meal was changed.');return false}
 saveActiveMealPlan();const before=captureGroceryCheckStates(),plan=mealPlans.find(plan=>plan.id===activePlanId),previousSlots=JSON.parse(JSON.stringify(weekSchedule(plan).slots)),undo=JSON.parse(captureState());
 undo.scheduleChangeUndo={sourceIds:[],checks:Object.fromEntries([...before].map(([id,item])=>[id,item.checked])),restoreOrder:false};snapshot(JSON.stringify(undo));
 const rememberedAmounts=heldWeekGroceryQuantities(plan),remembered=heldWeekGroceryChecks(plan);
 // Pin the underlying planner before hiding anything. Temporary IDs never enter
 // its overrides, reservations, linked activation, or Favorites score ledger.
 stabilizeAutomaticWeekSlots();update(plan);updateTemporaryGroceryChecks(plan,previousSlots,before);
 const sameCycle=new Map(before);for(const [id,checked]of Object.entries(remembered))if(!sameCycle.has(id))sameCycle.set(id,{checked,amount:rememberedAmounts[id]});
 saveActiveMealPlan();reconcileRotatedGroceryChecks(sameCycle,[]);persist();renderList();finishScheduleChangeUndo(undo);return true;
}
function leaveWeekEmpty(day,cat=null,wholeDay=false){
 return changeTemporaryWeek(plan=>{
  const state=editableWeekSchedule(plan);
  if(wholeDay){
   const entries=getDisplayedWeekdayMealsForPlan(plan,null,null,null,true).filter(entry=>entry.day===day),raw=plan.weekdayCategories?.[day],groups=(Array.isArray(raw)?raw:[raw]).filter(group=>cats.includes(group));
   const independent=entries.filter(entry=>entry.linkedTo==null);const keys=new Set([...groups.map(group=>temporarySlotKey(day,group)),...independent.map(entry=>temporarySlotKey(day,entry.cat)),...Object.keys(state.slots).filter(key=>key.startsWith(day+'::')&&(key===temporarySlotKey(day,null)||groups.some(group=>key===temporarySlotKey(day,group))))]);
   if(!keys.size)keys.add(temporarySlotKey(day,null));for(const key of keys)state.slots[key]={kind:'empty'};
  }else state.slots[temporarySlotKey(day,cat)]={kind:'empty'};
 });
}
function resumeWeekSlot(day,cat=null,wholeDay=false){return changeTemporaryWeek(plan=>{for(const key of Object.keys(weekSchedule(plan).slots))if(wholeDay?key.startsWith(day+'::'):key===temporarySlotKey(day,cat))delete plan.weekSchedule.slots[key]})}
function saveOneTimeMeal(day,cat,name,ingredients=[],existingId=null,details={}){
 const clean=String(name||'').trim();if(!clean)return false;
 return changeTemporaryWeek(plan=>{editableWeekSchedule(plan).slots[temporarySlotKey(day,cat)]={kind:'once',meal:{...details,id:existingId||'once-'+(crypto.randomUUID?.()||Date.now()+'-'+Math.random().toString(36).slice(2)),name:clean,cat:cat||'@day',rotation:false,temporaryMeal:true,ingredients:ingredients.map(line=>String(line).trim()).filter(Boolean)}}});
}
function fitOneTimeMealViewport(shade,box){
 const view=window.visualViewport;if(!view)return;
 const pageY=scrollY,pageX=scrollX,rootOverflow=document.documentElement.style.overflow,bodyOverflow=document.body.style.overflow;
 document.documentElement.style.overflow='hidden';document.body.style.overflow='hidden';box.style.overscrollBehavior='contain';
 let frame=0;
 const keepPage=()=>{if(shade.isConnected&&(scrollY!==pageY||scrollX!==pageX))window.scrollTo({left:pageX,top:pageY,behavior:'instant'})};
 window.addEventListener('scroll',keepPage,{passive:true});
 const reveal=()=>{
  const active=document.activeElement;if(!box.contains(active))return;
  let scroller=active.parentElement;while(scroller!==box&&scroller&&(!/(auto|scroll)/.test(getComputedStyle(scroller).overflowY)||scroller.scrollHeight<=scroller.clientHeight))scroller=scroller.parentElement;
  if(!scroller)return;const bounds=scroller.getBoundingClientRect(),field=active.getBoundingClientRect();
  if(shade.hasAttribute('data-viewer-recipe-draft')&&field.height>bounds.height-16)scroller.scrollTop+=field.top-bounds.top-8;else if(field.bottom>bounds.bottom-8)scroller.scrollTop+=field.bottom-bounds.bottom+8;
  else if(field.top<bounds.top+8)scroller.scrollTop-=bounds.top+8-field.top;
 };
 const fit=()=>{
  shade.style.inset='auto';shade.style.top=view.offsetTop+'px';shade.style.left=view.offsetLeft+'px';shade.style.width=view.width+'px';shade.style.height=view.height+'px';
  box.style.maxHeight=Math.max(80,view.height-36)+'px';box.style.overflowY='auto';
  cancelAnimationFrame(frame);frame=requestAnimationFrame(reveal);
 };
 const observer=new MutationObserver(()=>{if(!shade.isConnected){view.removeEventListener('resize',fit);view.removeEventListener('scroll',fit);box.removeEventListener('focusin',fit);window.removeEventListener('scroll',keepPage);cancelAnimationFrame(frame);document.documentElement.style.overflow=rootOverflow;document.body.style.overflow=bodyOverflow;window.scrollTo({left:pageX,top:pageY,behavior:'instant'});observer.disconnect()}});
 view.addEventListener('resize',fit);view.addEventListener('scroll',fit);box.addEventListener('focusin',fit);observer.observe(document.body,{childList:true});fit();
}
function openOneTimeMealEditor(day,cat,current=null){return openCreateScheduledRecipe({planId:activePlanId,day,category:cat==='@day'?null:cat,occasional:cat==='@day'||!getDayCategories(day).length},null,current)}
function slotEmptyLabel(day,cat){return 'Leave '+day+(getDayCategories(day).length>1&&cat&&cat!=='@day'?' '+cat.toLocaleLowerCase():'')+' empty'}
function compactMealDialog(title,label){
 const shade=document.createElement('div');shade.className='recipe-timer-dialog compact-meal-dialog';
 const box=document.createElement('div');box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label',label);
 const close=()=>shade.remove();appendRotationCloseHeader(box,title,close,true);
 shade.append(box);shade.onclick=e=>{if(e.target===shade)close()};shade.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();close()}};
 document.body.append(shade);return {shade,box,close};
}
function compactMealButton(dialog,label,action){
 const button=document.createElement('button');button.type='button';button.className='smallbtn meal-full-action';button.textContent=label;button.onclick=()=>{dialog.close();action()};dialog.box.append(button);return button;
}
function compactMealLinks(dialog,actions){
 const links=document.createElement('div');links.className='meal-quick-actions';
 actions.forEach(([label,action],index)=>{if(index){const dot=document.createElement('span');dot.textContent='·';dot.setAttribute('aria-hidden','true');links.append(dot)}const button=document.createElement('button');button.type='button';button.textContent=label;button.onclick=()=>{dialog.close();action()};links.append(button)});dialog.box.append(links);
}
function underlyingSlotMeal(plan,day,cat){return getDisplayedWeekdayMealsForPlan(plan,null,null,null,true).find(entry=>entry.day===day&&(cat==='@day'||cat==null||entry.cat===cat))}
function emptySlotAutomaticCandidate(day,cat){
 const plan=mealPlans.find(p=>p.id===activePlanId);if(!plan||!rotationGroupScheduled(plan,day,cat))return null;
 const entries=getDisplayedWeekdayMealsForPlan(plan,null,null,null,true),choice=plan.cycleSlotChoices?.[weekdaySlotKey(day,cat)];
 const candidates=automaticSlotCandidates(plan,day,cat,meals,entries).filter(meal=>!(choice?.excludedMealIds||[]).some(id=>String(id)===String(meal.id)));
 const used=new Set(mealPlans.flatMap(other=>getDisplayedWeekdayMealsForPlan(other,null,null,null,true).filter(entry=>other.id!==plan.id||entry.day!==day||entry.cat!==cat).map(entry=>String(entry.meal.id))));
 return candidates.find(meal=>!used.has(String(meal.id)))||candidates[0]||null;
}
function autoPopulateWeekSlot(day,cat){
 const meal=emptySlotAutomaticCandidate(day,cat);if(!meal)return false;
 applyManualWeekdayMeal(day,cat,meal,null,false,{automatic:true,schedulingOnly:true});return true;
}
function openUnscheduledGroupActions(day,cat){
 const dialog=compactMealDialog(day+' · '+cat,'Empty group options');
 compactMealButton(dialog,'Select Meal',()=>openWeekdayMealChooser(day,cat,null));
 if(emptySlotAutomaticCandidate(day,cat))compactMealButton(dialog,'Auto-Populate Meal',()=>autoPopulateWeekSlot(day,cat));
 compactMealButton(dialog,slotEmptyLabel(day,cat),()=>leaveWeekEmpty(day,cat));
 dialog.box.querySelector('button')?.focus();
}
function openWeekEmptyActions(day,cat){
 const dialog=compactMealDialog(day+' · Empty this week','Empty meal options'),plan=mealPlans.find(p=>p.id===activePlanId);
 compactMealButton(dialog,'Select Meal',()=>openWeekdayMealChooser(day,cat==='@day'?null:cat,null,cat==='@day'));
 if(emptySlotAutomaticCandidate(day,cat))compactMealButton(dialog,'Auto-Populate Meal',()=>autoPopulateWeekSlot(day,cat));
 if(underlyingSlotMeal(plan,day,cat))compactMealButton(dialog,'Resume planned meal',()=>resumeWeekSlot(day,cat));
}

function reorderableWeekEntries(){const entries=getDisplayedWeekdayMeals();return entries.filter(entry=>!(entry.linkedTo!=null&&!rotationGroupScheduled(mealPlans.find(p=>p.id===activePlanId),entry.day,entry.cat)&&entries.some(parent=>parent.day===entry.day&&String(parent.meal.id)===String(entry.linkedTo))))}
function setWeekDisplayOrder(day,keys){if(mealPersistence.paused)return false;saveActiveMealPlan();snapshot();const plan=mealPlans.find(p=>p.id===activePlanId);editableWeekSchedule(plan).order[day]=keys;saveActiveMealPlan();renderList();return true}
// Row gestures share one recognizer so a held drag cannot also open a recipe.
function bindWeekMealGestures(row,name,day,entry,openRecipe){
 const reorderable=()=>rows().length>1;
 let press=null,suppressUntil=0;
 const originalKey=scheduleDisplayKey(entry),rows=()=>[...document.querySelectorAll('[data-week-row][data-schedule-day]')].filter(w=>w.dataset.scheduleDay===day);
 const begin=(e,x,y,source,id)=>{
  if(press||e.target.closest('button,input,a,select')&&!e.target.closest('.mealname,.top-meal-inline-category'))return;
  press={x,y,source,id,phase:'pending',scroll:scrollY,ordered:null,onName:!!e.target.closest('.mealname')};
  const current=press;current.timer=setTimeout(()=>{if(press===current&&Math.abs(scrollY-current.scroll)<3)current.phase='held'},550);
 };
 const move=(e,x,y)=>{
  if(!press)return;const distance=Math.hypot(x-press.x,y-press.y);
  if(press.phase==='pending'&&distance>8){clearTimeout(press.timer);press.phase='scroll'}
  if(press.phase==='held'&&distance>10)press.phase=reorderable()?'drag':'scroll';
  if(['held','drag'].includes(press.phase)&&e.cancelable===false){clearTimeout(press.timer);press.phase='scroll'}
  if(!['held','drag'].includes(press.phase))return;
  e.preventDefault();e.stopImmediatePropagation();
  if(press.phase!=='drag')return;
  if(press.source==='pointer'&&!row.hasPointerCapture(press.id))row.setPointerCapture(press.id);
  row.style.opacity='.55';const target=rows().find(w=>{const r=w.getBoundingClientRect();return y>=r.top&&y<=r.bottom});
  if(!target||target.dataset.displayKey===originalKey)return;
  const rect=target.getBoundingClientRect(),keys=rows().map(w=>w.dataset.displayKey).filter(k=>k!==originalKey),index=keys.indexOf(target.dataset.displayKey)+(y>rect.top+rect.height/2?1:0);
  keys.splice(index,0,originalKey);press.ordered=keys;
  for(const wrap of rows())wrap.style.outline=wrap===target?'2px solid #8397b5':'';
 };
 const finish=(e,cancel=false)=>{
  if(!press)return;const current=press;press=null;clearTimeout(current.timer);row.style.opacity='';for(const wrap of rows())wrap.style.outline='';
  if(current.phase==='pending'&&!cancel)return;
  suppressUntil=Date.now()+700;if(e.cancelable)e.preventDefault();e.stopImmediatePropagation();
  if(cancel)return;
  if(current.phase==='drag'){if(current.ordered)setWeekDisplayOrder(day,current.ordered)}
  else if(current.phase==='held'&&current.onName&&entry.meal&&!entry.meal.temporaryMeal)openRecipe();
 };
 row.addEventListener('touchstart',e=>{if(e.touches.length!==1){if(press)finish(e,true);return}const t=e.changedTouches[0];begin(e,t.clientX,t.clientY,'touch',t.identifier)},{capture:true,passive:true});
 row.addEventListener('touchmove',e=>{if(press?.source!=='touch')return;const t=[...e.changedTouches].find(t=>t.identifier===press.id);if(t)move(e,t.clientX,t.clientY)},{capture:true,passive:false});
 row.addEventListener('touchend',e=>{if(press?.source==='touch')finish(e)},{capture:true,passive:false});
 row.addEventListener('touchcancel',e=>{if(press?.source==='touch')finish(e,true)},{capture:true,passive:false});
 row.addEventListener('pointerdown',e=>{if(e.pointerType==='touch'||e.button!==0)return;begin(e,e.clientX,e.clientY,'pointer',e.pointerId)},{capture:true});
 row.addEventListener('pointermove',e=>{if(press?.source==='pointer')move(e,e.clientX,e.clientY)},{capture:true});
 row.addEventListener('pointerup',e=>{if(press?.source==='pointer')finish(e)},{capture:true});
 for(const event of ['pointercancel','lostpointercapture'])row.addEventListener(event,e=>{if(press?.source==='pointer')finish(e,true)},{capture:true});
 row.addEventListener('click',e=>{if(Date.now()<suppressUntil){e.preventDefault();e.stopImmediatePropagation()}},{capture:true});
 row.addEventListener('contextmenu',e=>e.preventDefault());
 name.addEventListener('keydown',e=>{if(!e.altKey||!['ArrowUp','ArrowDown'].includes(e.key)||!reorderable())return;e.preventDefault();const keys=rows().map(w=>w.dataset.displayKey),from=keys.indexOf(originalKey),to=from+(e.key==='ArrowUp'?-1:1);if(to<0||to>=keys.length)return;[keys[from],keys[to]]=[keys[to],keys[from]];setWeekDisplayOrder(day,keys);[...document.querySelectorAll('[data-week-row]')].find(w=>w.dataset.scheduleDay===day&&w.dataset.displayKey===originalKey)?.querySelector('.mealname')?.focus({preventScroll:true})});
}

function getDisplayedWeekdayMealsForPlan(plan, priorUsedByGroup=null, savedSchedule=null, reservedByGroup=null, ignoreTemporary=false){
 const library=savedSchedule?savedSchedule.meals:meals,categories=savedSchedule?savedSchedule.cats:cats,plans=savedSchedule?savedSchedule.mealPlans:mealPlans,tabsVisible=savedSchedule?savedSchedule.showMealPlanTabs:showMealPlanTabs;
 const start=savedSchedule?weekdays.indexOf(savedSchedule.startWeekday):0;
 const days=savedSchedule?weekdays.slice(start<0?0:start).concat(weekdays.slice(0,start<0?0:start)):orderedDays();
 const schedulingPlans=plans.map(other=>String(other.id)===String(plan.id)?plan:!savedSchedule&&other.id===activePlanId?{...other,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:other);
 const shown=allocateScheduledWeek(library,categories,schedulingPlans,days,plan.id,reservedByGroup).get(String(plan.id))||[];
 // Linked recipes follow the chosen main recipe, replacing an assigned group's
 // normal choice without changing the underlying rotation order.
 const result=[];
 for(const day of days){
  const dayEntries=shown.filter(entry=>entry.day===day);
  const originalIds=new Set(dayEntries.map(entry=>String(entry.meal.id)));
  const additions=[];
  const replacements=new Map();
  const visited=new Set(originalIds);
  for(const entry of dayEntries){
   const ids=Array.isArray(entry.meal.linkedMealIds)?entry.meal.linkedMealIds:[];
   for(const targetId of ids){
    const target=library.find(m=>String(m.id)===String(targetId));
    if(!target||String(target.id)===String(entry.meal.id)||visited.has(String(target.id)))continue;
    const placement=linkedRecipePlacement(plan,day,entry,target,dayEntries,library);
    if((plan.cycleSlotChoices?.[weekdaySlotKey(day,placement)]?.excludedMealIds||[]).some(id=>String(id)===String(target.id)))continue;
    const slot=dayEntries.find(e=>e.cat===placement),choice=plan.cycleSlotChoices?.[weekdaySlotKey(day,placement)];
    const applies=slot&&choice&&(choice.mealId==null||String(choice.mealId)===String(slot.meal.id));
    if(slot&&manualWeekdayMealChoice(plan,day,placement,slot.meal.id)||applies&&(choice.retain||(choice.blockedParents||[]).some(id=>String(id)===String(entry.meal.id))))continue;
    visited.add(String(target.id));
    const linked={day,cat:placement,meal:target,linkedTo:entry.meal.id,...(entry.occasional&&!rotationGroupScheduled(plan,day,target.cat)?{occasional:true}:{}),scheduledSlot:rotationGroupScheduled(plan,day,placement),...(pairedMainGroup(plan,day,placement)?{dependentSide:true}:{})};
    if(slot){
     if(!replacements.has(placement))replacements.set(placement,linked);
    }else additions.push(linked);
   }
  }
  const emitted=new Set();
  for(const entry of dayEntries){
   const current=replacements.get(entry.cat)||entry;
   if(!emitted.has(String(current.meal.id))||current.linkedTo==null&&rotationGroupScheduled(plan,day,current.cat)){result.push(current);emitted.add(String(current.meal.id))}
   for(const addition of additions.filter(x=>String(x.linkedTo)===String(entry.meal.id))){
    if(!emitted.has(String(addition.meal.id))){result.push(addition);emitted.add(String(addition.meal.id))}
   }
  }
 }
 return ignoreTemporary?result:applyWeekSchedule(plan,result,days);
}
// Keep linked side dishes in rotation and immediately ahead of their group's queue.
// Only newly activated links are promoted; ordinary renders never reorder them.
let previouslyActiveLinkedIds=new Set();
function reconcileActiveLinkedMeals(){
 const activeLinks=new Set(),automaticLinks=new Set();
 for(const plan of mealPlans){
  const entries=getDisplayedWeekdayMealsForPlan(plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan,null,null,null,true);
  for(const entry of entries){
   if(entry.linkedTo!=null&&!entry.occasional&&String(plan.occasionalMeals?.[entry.day])!==String(entry.linkedTo)){activeLinks.add(String(entry.meal.id));if(rotationAdvancesRecipe(entry,plan,entries))automaticLinks.add(String(entry.meal.id))}
  }
 }
 let changed=false;
 for(const targetId of activeLinks){
  const target=meals.find(m=>String(m.id)===targetId);
  if(!target?.cat||!automaticLinks.has(targetId)||target.keepAsIdea===true&&!target.rotation)continue;
  const newlyActivated=!previouslyActiveLinkedIds.has(targetId);
  if(!target.rotation){target.rotation=true;changed=true}
  if(newlyActivated){
   const from=meals.indexOf(target);
   if(from>=0){
    meals.splice(from,1);
    const first=meals.findIndex(m=>m.cat===target.cat&&m.rotation);
    if(first<0)meals.push(target);else meals.splice(first,0,target);
    changed=true;
   }
  }
 }
 previouslyActiveLinkedIds=activeLinks;
 if(changed)persist();
}
function getDisplayedWeekdayMeals(){
 return getDisplayedWeekdayMealsForPlan({...mealPlans.find(p=>p.id===activePlanId),id:activePlanId,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters});
}
// Keep grocery-list membership independent from checked-off grocery items.
// Only a meal ENTERING Top Recipes gets new unchecked source quantities;
// never clear mealRotationSelectedIngredientsV1, which determines what remains
// on the grocery list. The current plan is persisted so view changes do not
// repeatedly uncheck the same ingredients.
function resetGroceriesForNewTopMeals(previousIdsOverride=null){
  const storageKey='mealRotationLastTopMealIdsV1:'+activePlanId;
  const currentIds=[...new Set(getDisplayedWeekdayMeals().map(({meal})=>String(meal.id)))];
  let previousIds=null;
  if(previousIdsOverride!==null){
    previousIds=new Set([...previousIdsOverride].map(String));
  }else{
    try{
      const stored=JSON.parse(localStorage.getItem(storageKey)||'null');
      if(Array.isArray(stored))previousIds=new Set(stored.map(String));
    }catch(e){}
  }
  if(previousIds){
    const enteringIds=currentIds.filter(mealId=>!previousIds.has(mealId));
    if(enteringIds.length){
      const entering=new Set(enteringIds);
      for(const source of getGroceryContributions(true))if(source.planId===activePlanId&&entering.has(String(source.mealId))&&typeof groceryOccurrenceChecks.checks[source.id]!=='boolean')groceryOccurrenceChecks.checks[source.id]=false;
      saveGroceryOccurrenceChecks();
    }
  }
  // An existing installation should not lose checks just for loading this file.
  try{localStorage.setItem(storageKey,JSON.stringify(currentIds))}catch(e){}
}
// Reordering the shared recipe library must not switch the displayed meal in another plan.
// Category renames/deletions also update meal plans not currently selected.
function updateOtherMealPlansForCategory(category,replacement=null){
 saveActiveMealPlan();
 // Temporary slots and display keys follow an explicit group rename/removal.
 for(const plan of mealPlans)if(plan.weekSchedule){
  for(const day of weekdays){const old=temporarySlotKey(day,category),next=temporarySlotKey(day,replacement),item=plan.weekSchedule.slots[old];if(item){if(replacement&&!plan.weekSchedule.slots[next]){plan.weekSchedule.slots[next]=item;if(item.meal)item.meal.cat=replacement}delete plan.weekSchedule.slots[old]}
   const order=plan.weekSchedule.order[day];if(order)plan.weekSchedule.order[day]=[...new Set(order.flatMap(key=>{try{const parts=JSON.parse(key);if(parts[0]!==category)return [key];if(!replacement)return [];parts[0]=replacement;return [JSON.stringify(parts)]}catch(e){return [key]}}))];
  }
 }

 for(const plan of mealPlans){
  if(plan.id===activePlanId)continue;
  const assignments=plan.weekdayCategories||{};
  const overrides=plan.weekdayMealOverrides||{};
  for(const day of weekdays){
   const raw=assignments[day];const entries=(Array.isArray(raw)?raw:[raw]).filter(Boolean);
   if(!entries.includes(category))continue;
   assignments[day]=[...new Set(entries.flatMap(c=>c===category?(replacement?[replacement]:[]):[c]))];
   const oldKey=weekdaySlotKey(day,category);
   if(overrides[oldKey]!==undefined){
    if(replacement)overrides[weekdaySlotKey(day,replacement)]=overrides[oldKey];
    delete overrides[oldKey];
   }
   if(entries[0]===category)delete overrides[day];
  }
  plan.weekdayCategories=assignments;plan.weekdayMealOverrides=overrides;
  if(Array.isArray(plan.pinnedCats))plan.pinnedCats=[...new Set(plan.pinnedCats.flatMap(c=>c===category?(replacement?[replacement]:[]):[c]))];
 }
 saveActiveMealPlan();
}
function preserveOtherMealPlanChoices(day,category,capturedSchedules=null){
 saveActiveMealPlan();
 const schedules=capturedSchedules||new Map(mealPlans.map(plan=>[plan.id,getDisplayedWeekdayMealsForPlan(plan)]));
 for(const plan of mealPlans){
  rememberDependentSideState(plan,schedules.get(plan.id)||[]);plan.weekdayMealOverrides={...(plan.weekdayMealOverrides||{})};plan.cycleRetainedSlots={...(plan.cycleRetainedSlots||{})};plan.cycleSlotChoices={...(plan.cycleSlotChoices||{})};
  for(const item of schedules.get(plan.id)||[]){
   if(item.scheduleOnly||!rotationSelectable(item,plan)||(plan.id===activePlanId&&item.day===day&&item.cat===category))continue;
   const key=weekdaySlotKey(item.day,item.cat),id=String(item.meal.id),old=plan.cycleSlotChoices[key],manual=manualWeekdayMealChoice(plan,item.day,item.cat,id);
   plan.weekdayMealOverrides[key]=id;plan.cycleRetainedSlots[key]=id;
   plan.cycleSlotChoices[key]={...(old&&String(old.mealId)===id?old:{}),...(manual?{substitution:true,retain:true}:{}),...(day!=null?{retain:true}:{}),mealId:id,parentId:String(item.linkedTo??'')};
  }
 }
 weekdayMealOverrides={...(mealPlans.find(plan=>plan.id===activePlanId)?.weekdayMealOverrides||{})};
}
// Capture the whole schedule before a shared queue changes. Promotion replaces
// one unprotected active-plan slot; all other plan/weekday choices remain exact.
function prepareRecipePromotion(meal,pin=true){
 saveActiveMealPlan();
 const schedules=new Map(mealPlans.map(plan=>[plan.id,getDisplayedWeekdayMealsForPlan(plan)]));
 const plan=mealPlans.find(p=>p.id===activePlanId),entries=schedules.get(plan.id),grocery=captureGroceryCheckStates();
 const alreadyScheduled=[...schedules.values()].some(entries=>entries.some(item=>String(item.meal.id)===String(meal.id)));
 const candidates=alreadyScheduled?[]:orderedDays().filter(day=>{
  if(!rotationGroupScheduled(plan,day,meal.cat)||!recipeMatchesFilters(meal,plan.weekdayRecipeFilters?.[weekdaySlotKey(day,meal.cat)]||[]))return false;
  const current=entries.find(item=>item.day===day&&item.cat===meal.cat);
  if(!automaticSlotCandidates(plan,day,meal.cat,[...meals.filter(m=>String(m.id)!==String(meal.id)),{...meal,rotation:true}],entries).some(candidate=>String(candidate.id)===String(meal.id)))return false;
  const linked=current&&(current.linkedTo!=null||entries.some(parent=>parent.day===day&&parent!==current&&(parent.meal.linkedMealIds||[]).some(id=>String(id)===String(current.meal.id))));
  return !manualWeekdayMealChoice(plan,day,meal.cat)&&!current?.occasional&&!linked;
 });
 const today=new Date();today.setHours(0,0,0,0);
 function score(day){const current=entries.find(item=>item.day===day&&item.cat===meal.cat);if(!current)return Infinity;const date=recipeLastCookedTime(current.meal);return date!==null&&date<=today.getTime()?date:-Infinity}
 // Stable sorting leaves equal/unknown dates in the configured weekday order.
 candidates.sort((a,b)=>{const x=score(a),y=score(b);return x===y?0:x>y?-1:1});const day=candidates[0]||null;
 if(pin)preserveOtherMealPlanChoices(null,null,schedules);
 return {day,grocery,schedules,pinned:pin};
}
function finishRecipePromotion(meal,before){
 if(!before.pinned)preserveOtherMealPlanChoices(null,null,before.schedules);
 const plan=mealPlans.find(p=>p.id===activePlanId);
 meal.rotationPromotionPriority=Math.max(Date.now(),...meals.map(m=>Number(m.rotationPromotionPriority)||0))+1;
 for(const p of mealPlans)for(const choice of Object.values(p.cycleSlotChoices||{}))if(Array.isArray(choice.excludedMealIds))choice.excludedMealIds=choice.excludedMealIds.filter(id=>String(id)!==String(meal.id));
 if(before.day){
  const key=weekdaySlotKey(before.day,meal.cat),id=String(meal.id);
  setWeekdayOverride(before.day,meal.cat,id);
  plan.cycleRetainedSlots={...(plan.cycleRetainedSlots||{}),[key]:id};
  plan.cycleSlotChoices={...(plan.cycleSlotChoices||{}),[key]:{mealId:id,parentId:'',blockedParents:[]}};
 }
 saveWeekdayMealOverrides();reconcileActiveLinkedMeals();reconcileRotatedGroceryChecks(before.grocery,[]);
}
function promoteMealToRotation(meal){
 if(!meal.cat||meal.rotation)return;
 if(groceryCheckStorageInvalid){showAppMessage('Saved grocery check states could not be read. Export a backup before repairing this browser data.');return}
 snapshot();const before=prepareRecipePromotion(meal);
 meal.rotation=true;const from=meals.indexOf(meal);if(from>=0)meals.splice(from,1);
 const first=meals.findIndex(m=>m.cat===meal.cat&&m.rotation);if(first<0)meals.push(meal);else meals.splice(first,0,meal);
 finishRecipePromotion(meal,before);persist();renderList();
}
// Section moves reuse occurrence-aware scheduling and groceries without cooking events.
function prepareRecipeDemotion(){saveActiveMealPlan();return {schedules:new Map(mealPlans.map(p=>[p.id,queueWeekEntries(p)])),grocery:captureGroceryCheckStates()}}
function demoteMealToIdeas(meal,updateRecipe=null,prepared=null){
 if(!meal.rotation&&!updateRecipe)return;
 if(groceryCheckStorageInvalid){showAppMessage('Saved grocery check states could not be read. Export a backup before repairing this browser data.');return}
 const {schedules,grocery}=prepared||prepareRecipeDemotion();
 // The recipe editor already captured one undo snapshot before applying its fields.
 if(!prepared)snapshot();if(updateRecipe)updateRecipe();preserveOtherMealPlanChoices(null,null,schedules);meal.rotation=false;delete meal.rotationPromotionPriority;
 const position=meals.indexOf(meal);if(position>=0){meals.splice(position,1);meals.push(meal)}
 detachRecipeOccurrences(new Set([String(meal.id)]),schedules,grocery);persist();renderList();
}
function recipeSectionMoveButton(meal){
 const button=document.createElement('button');button.type='button';button.className='recipe-section-move';
 const label='Move '+(meal.name||'meal')+' to '+(meal.rotation?'Ideas':'rotation');button.title=label;button.setAttribute('aria-label',label);
 button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="'+(meal.rotation?'m6 10 6 6 6-6M12 16V3':'m6 14 6-6 6 6M12 8v13')+'"/></svg>';
 button.onclick=e=>{e.preventDefault();e.stopPropagation();const wasRotation=meal.rotation;if(wasRotation)demoteMealToIdeas(meal);else promoteMealToRotation(meal);if(meal.rotation!==wasRotation&&setMasterRecipeSectionOpen(meal.cat,meal.rotation,true))renderList()};return button;
}
// A recipe rotating out advances in every plan where it was being shown.
// Other visible recipes are preserved with explicit overrides so a category
// reorder does not unexpectedly rotate unrelated Breakfast/Lunch/Dinner meals.
// One-step restore of the display immediately before the most recent rotation.
// Kept separately from general Undo so the dedicated arrow remains available after a reload.
// Shared close header for the rotation menus and their empty-history message.
function appendRotationCloseHeader(panel,message,dismiss,compact=false){
 const header=document.createElement('div');header.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:'+(compact?'0':'18px');
 const heading=document.createElement('h3');heading.textContent=message;heading.style.cssText='font-size:19px;font-weight:600;margin:0;min-width:0;flex:1;overflow-wrap:anywhere';
 const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close');close.style.cssText+=';width:44px;height:44px;min-width:44px;min-height:44px;flex:0 0 44px';close.onclick=dismiss;
 header.append(heading,close);panel.append(header);
}
function showNoPreviousRotation(){
 const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;z-index:20000;background:#0008;display:flex;align-items:center;justify-content:center;padding:18px';
 const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','No previous rotation to restore.');panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:16px 18px;width:100%;max-width:480px;box-shadow:0 12px 36px #0003';
 appendRotationCloseHeader(panel,'No previous rotation to restore.',()=>overlay.remove(),true);
 overlay.append(panel);overlay.addEventListener('click',event=>{if(event.target===overlay)overlay.remove()});overlay.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();overlay.remove()}});document.body.append(overlay);panel.querySelector('button').focus({preventScroll:true});
}
const ROTATION_BACK_KEY='mealRotationLastRotationBeforeV1';
function rotateAllBack(){
 const previous=readPreviousRotation();if(!previous){showNoPreviousRotation();return}
 const slots=restorableRotationSlots(previous);if(!slots.length){showNoPreviousRotation();return}
 rotateSelectedBack(slots.map(rotationSlotKey),true);
}
// Offer all/select choices; closing leaves the one-step rotation history intact.
function openRotateBackOptions(){
 const previous=readPreviousRotation();
 if(!previous){showNoPreviousRotation();return;}
 const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:10002;display:flex;align-items:center;justify-content:center;padding:18px';
 const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Rotate back recipes');panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:22px;width:100%;max-width:480px;box-shadow:0 12px 36px #0003';
 appendRotationCloseHeader(panel,'Rotate back recipes',()=>overlay.remove());
 const actions=document.createElement('div');actions.style.cssText='display:flex;flex-direction:column;gap:12px';
 [['Rotate back all recipes',rotateAllBack],['Select recipes to rotate back',openRotateBackChooser]].forEach(([label,action])=>{const button=document.createElement('button');button.type='button';button.className='smallbtn';button.textContent=label;button.style.cssText='padding:12px 14px;width:100%;font-size:16px';button.onclick=()=>{overlay.remove();action()};actions.append(button)});
 panel.append(actions);overlay.append(panel);overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});overlay.addEventListener('keydown',e=>{if(e.key==='Escape')overlay.remove()});document.body.append(overlay);
}
function readPreviousRotation(){
 try{const value=JSON.parse(localStorage.getItem(ROTATION_BACK_KEY)||'null');return value&&Array.isArray(value.meals)&&Array.isArray(value.mealPlans)?value:null}catch(e){return null}
}
function rotationGroupScheduled(plan,day,cat){const raw=plan?.weekdayCategories?.[day];return (Array.isArray(raw)?raw:[raw]).includes(cat)}
function rotationSelectable(item,plan){if(item.scheduleOnly)return true;if(item.occasional)return false;return item.scheduledSlot===true||rotationGroupScheduled(plan,item.day,item.cat)||(item.linkedTo==null&&!item.parentId)}
function cycleAffectedEntries(entries,selected,plan){
 const keys=new Set(selected.map(rotationOccurrenceKey));
 return entries.filter(item=>keys.has(rotationOccurrenceKey(item))||selected.some(owner=>!owner.scheduleOnly&&owner.day===item.day&&pairedMainGroup(plan,item.day,item.cat)===owner.cat)||(!rotationGroupScheduled(plan,item.day,item.cat)&&item.linkedTo!=null&&selected.some(owner=>owner.day===item.day&&String(owner.meal?.id??owner.mealId)===String(item.linkedTo))));
}
function previousRotationSlots(previous){
 const entries=Array.isArray(previous.rotationOccurrences)?previous.rotationOccurrences.map(item=>({...item,meal:previous.meals.find(m=>String(m.id)===String(item.mealId))||(item.scheduleOnly?rotationWeekEntries(previous.mealPlans.find(p=>p.id===item.planId),previous).find(entry=>entry.day===item.day&&entry.cat===item.cat)?.meal:null)})).filter(item=>item.meal):previous.mealPlans.flatMap(plan=>rotationWeekEntries(plan,previous).map(item=>({...item,planId:plan.id,planName:plan.name})));
 return entries.filter(item=>rotationSelectable(item,previous.mealPlans.find(p=>p.id===item.planId)));
}
function rotationOccurrenceKey(item){return cookingOccurrenceKey({planId:String(item.planId),day:item.day,mealId:String(item.meal?.id??item.mealId),parentId:String(item.parentId??item.linkedTo??'')})}
function rotationSlotKey(item){return item.planId+'||'+weekdaySlotKey(item.day,item.cat)}
// A history snapshot supplies scheduling choices, never recipe records.
function restorableRotationSlots(previous){
 return previousRotationSlots(previous).filter(item=>{
  const plan=mealPlans.find(p=>p.id===item.planId),meal=meals.find(m=>String(m.id)===String(item.meal.id));
  if(item.scheduleOnly)return !!plan&&!!weekSchedule(previous.mealPlans.find(p=>p.id===item.planId)).slots[temporarySlotKey(item.day,item.cat)]&&(item.cat==='@day'||cats.includes(item.cat));
  if(!plan||!meal||!rotationGroupScheduled(plan,item.day,item.cat))return false;
  const old=previous.mealPlans.find(p=>p.id===item.planId),substitution=manualWeekdayMealChoice(old,item.day,item.cat,item.meal.id),dependent=!!pairedMainGroup(old,item.day,item.cat);
  return substitution||meal.rotation&&(meal.cat===item.cat||dependent);
 });
}
function rotateSelectedBack(selected,restoreAll=false){
 const previous=readPreviousRotation();if(!previous||!selected.length)return;
 saveActiveMealPlan();
 const beforeIds=new Set(getDisplayedWeekdayMeals().map(({meal})=>String(meal.id)));
 const priorSlots=restorableRotationSlots(previous),requested=priorSlots.filter(item=>selected.includes(rotationSlotKey(item))),desired=priorSlots.filter(item=>cycleAffectedEntries([item],requested.filter(owner=>owner.planId===item.planId),previous.mealPlans.find(plan=>plan.id===item.planId)).length);
 if(!desired.length)return;
 const restoringSlots=new Set(desired.map(rotationSlotKey));
 const retained=new Map(mealPlans.map(plan=>[plan.id,getDisplayedWeekdayMealsForPlan(plan).filter(item=>rotationSelectable(item,plan)&&!restoringSlots.has(rotationSlotKey({...item,planId:plan.id})))]));
 const groceryBefore=captureGroceryCheckStates();
 if(restoreAll)clearCookingForCycleBack(previous);else clearCookingForSlots(desired);
 snapshot();
 for(const plan of mealPlans){const overrides={...(plan.weekdayMealOverrides||{})},pins={...(plan.cycleRetainedSlots||{})},choices={...(plan.cycleSlotChoices||{})};for(const item of retained.get(plan.id)||[]){if(item.scheduleOnly)continue;const key=weekdaySlotKey(item.day,item.cat);overrides[key]=String(item.meal.id);pins[key]=String(item.meal.id);const old=choices[key],valid=old&&String(old.mealId)===String(item.meal.id),manual=manualWeekdayMealChoice(plan,item.day,item.cat,item.meal.id);choices[key]={...(valid?old:{}),...(manual?{substitution:true}:{}),mealId:String(item.meal.id),parentId:String(item.linkedTo??''),retain:manual||desired.some(x=>x.planId===plan.id&&x.day===item.day)||!!(valid&&old.retain),blockedParents:valid?old.blockedParents||[]:[]}}plan.weekdayMealOverrides=overrides;plan.cycleRetainedSlots=pins;plan.cycleSlotChoices=choices;}
 // Keep unselected meals and current edits intact; restore only selected slots.
 for(const item of desired){
  const plan=mealPlans.find(p=>p.id===item.planId);
  if(item.scheduleOnly){
   const old=previous.mealPlans.find(p=>p.id===item.planId),key=temporarySlotKey(item.day,item.cat);editableWeekSchedule(plan).slots[key]=JSON.parse(JSON.stringify(old.weekSchedule.slots[key]));
   // Rotating a hidden slot may reopen its deferred original. Restore the
   // underlying choice as well as the empty/one-time presentation on Rotate Back.
   const keys=item.cat==='@day'?new Set(['weekdayMealOverrides','cycleRetainedSlots','cycleSlotChoices'].flatMap(field=>Object.keys(old[field]||{}).concat(Object.keys(plan[field]||{}))).filter(key=>key.startsWith(item.day+'::'))):new Set([weekdaySlotKey(item.day,item.cat)]);
   const raw=plan.weekdayCategories?.[item.day],groups=Array.isArray(raw)?raw:[raw];if(item.cat==='@day'||groups[0]===item.cat)keys.add(item.day);
   for(const field of ['weekdayMealOverrides','cycleRetainedSlots','cycleSlotChoices'])for(const key of keys){
    plan[field]={...(plan[field]||{})};if(Object.hasOwn(old[field]||{},key))plan[field][key]=JSON.parse(JSON.stringify(old[field][key]));else delete plan[field][key];
   }
   continue;
  }
  clearTemporarySlot(plan,item.day,item.cat);
  const priorPlan=previous.mealPlans.find(p=>p.id===item.planId),priorChoice=priorPlan?.cycleSlotChoices?.[weekdaySlotKey(item.day,item.cat)],dependent=!!pairedMainGroup(priorPlan,item.day,item.cat),substitution=priorPlan?.cycleSlotChoices?.[weekdaySlotKey(item.day,item.cat)]?.substitution===true||!!(dependent&&plan&&!pairedMainGroup(plan,item.day,item.cat)&&item.meal.cat!==item.cat);
  if(!plan||!meals.some(m=>String(m.id)===String(item.meal.id)&&(substitution||(m.rotation&&(m.cat===item.cat||dependent)))))continue;
  const overrides={...(plan.weekdayMealOverrides||{})};
  const raw=(plan.weekdayCategories||{})[item.day];const groups=Array.isArray(raw)?raw:[raw];
  if(groups[0]===item.cat)delete overrides[item.day];
  overrides[weekdaySlotKey(item.day,item.cat)]=String(item.meal.id);
  plan.cycleRetainedSlots={...(plan.cycleRetainedSlots||{}),[weekdaySlotKey(item.day,item.cat)]:String(item.meal.id)};
  // Preserve the saved choice metadata, including paired-side queue protection;
  // validate IDs against current recipes rather than restoring recipe records.
  plan.cycleSlotChoices={...(plan.cycleSlotChoices||{}),[weekdaySlotKey(item.day,item.cat)]:{...(String(priorChoice?.mealId)===String(item.meal.id)?JSON.parse(JSON.stringify(priorChoice)):{}),...(substitution?{substitution:true}:{}),mealId:String(item.meal.id),parentId:(()=>{const parent=String(item.parentId??item.linkedTo??'');return meals.some(m=>String(m.id)===parent&&(m.linkedMealIds||[]).some(id=>String(id)===String(item.meal.id)))?parent:''})(),retain:true}};
  plan.weekdayMealOverrides=overrides;
 }
 // Restore linked children's positions from the saved pre-cycle order.
 const restoringIds=new Set(desired.filter(item=>rotationAdvancesRecipe(item,previous.mealPlans.find(plan=>plan.id===item.planId),rotationWeekEntries(previous.mealPlans.find(plan=>plan.id===item.planId),previous))).map(item=>String(item.meal.id)));
 for(const item of desired.filter(item=>rotationAdvancesRecipe(item,previous.mealPlans.find(plan=>plan.id===item.planId))))for(const linkedId of (Array.isArray(item.meal.linkedMealIds)?item.meal.linkedMealIds:[]))restoringIds.add(String(linkedId));
 for(const item of desired){const meal=meals.find(m=>String(m.id)===String(item.meal.id)),prior=previous.meals.find(m=>String(m.id)===String(item.meal.id));if(meal?.rotation&&meal.rotationPromotionPriority==null&&Number.isFinite(prior?.rotationPromotionPriority))meal.rotationPromotionPriority=prior.rotationPromotionPriority;}
 for(const cat of new Set(previous.meals.filter(m=>restoringIds.has(String(m.id))).map(m=>m.cat))){
  const priorOrder=previous.meals.filter(m=>m.cat===cat&&m.rotation).map(m=>String(m.id));
  const currentSlots=[];
  meals.forEach((m,i)=>{if(m.cat===cat&&m.rotation)currentSlots.push(i)});
  const current=currentSlots.map(i=>meals[i]);
  const rank=id=>priorOrder.indexOf(String(id));
  const restored=current.filter(m=>restoringIds.has(String(m.id))).sort((a,b)=>rank(a.id)-rank(b.id));
  const remaining=current.filter(m=>!restoringIds.has(String(m.id)));
  const reordered=restored.concat(remaining);
  currentSlots.forEach((slot,i)=>{meals[slot]=reordered[i]});
 }
 const restoredEntries=previous.mealPlans.flatMap(plan=>cycleAffectedEntries(getDisplayedWeekdayMealsForPlan(plan,null,previous).map(item=>({...item,planId:plan.id})),desired.filter(item=>item.planId===plan.id),plan));
 applyRestoredCookedDates(meals,restoredRotationCookedDates(previous,new Set(restoredEntries.map(rotationOccurrenceKey))));
 restoreRotationCalendarSlots(previous,desired);restoreFavoriteRotationTurns(previous,desired);
 if(restoreAll)for(const plan of mealPlans){const old=previous.mealPlans.find(p=>p.id===plan.id);for(const day of new Set(desired.filter(item=>item.planId===plan.id).map(item=>item.day))){const order=old?.weekSchedule?.order?.[day];if(order&&!weekSchedule(plan).order[day])editableWeekSchedule(plan).order[day]=[...order]}}
 if(desired.some(item=>rotationAdvancesRecipe(item,previous.mealPlans.find(p=>p.id===item.planId))))previouslyActiveLinkedIds=new Set();
 const activePlan=mealPlans.find(p=>p.id===activePlanId);
 weekdayMealOverrides={...(activePlan?.weekdayMealOverrides||{})};saveWeekdayMealOverrides();
 try{localStorage.removeItem(ROTATION_BACK_KEY)}catch(e){}
 const groceryRestored=mealPlans.flatMap(plan=>cycleAffectedEntries((getDisplayedWeekdayMealsForPlan(plan)).map(item=>({...item,planId:plan.id})),desired.filter(item=>item.planId===plan.id),plan));
 if(restoreAll){checkedIngredients=new Set(previous.checkedIngredients||[]);localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));}
 reconcileRotatedGroceryChecks(groceryBefore,groceryRestored,previous);
 resetGroceriesForNewTopMeals(beforeIds);topIngredientExpanded.clear();topIngredientManualHiddenOverride.clear();persist();renderTabs();renderList();
}
function openRotateBackChooser(){
 const previous=readPreviousRotation();if(!previous){showNoPreviousRotation();return;}
 const currentPlans=new Map(mealPlans.map(plan=>[plan.id,getDisplayedWeekdayMealsForPlan(plan)]));
 const choices=restorableRotationSlots(previous).filter(item=>{
  const plan=mealPlans.find(p=>p.id===item.planId);if(!plan)return false;
  const now=(currentPlans.get(item.planId)||[]).find(x=>x.day===item.day&&x.cat===item.cat);
  if(item.scheduleOnly){const old=previous.mealPlans.find(p=>p.id===item.planId),key=temporarySlotKey(item.day,item.cat);return JSON.stringify(weekSchedule(plan).slots[key]??null)!==JSON.stringify(weekSchedule(old).slots[key]??null)}
  return now&&String(now.meal.id)!==String(item.meal.id);
 });
 if(!choices.length){appDialog('Meals already match the previous rotation.','','alert');return;}
 const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:10002;display:flex;align-items:center;justify-content:center;padding:16px';
 const box=document.createElement('div');box.style.cssText='background:white;color:#222;border-radius:14px;padding:18px;max-width:520px;width:100%;max-height:82vh;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 8px 30px #0004';
 const title=document.createElement('h3');title.textContent='Select meals to rotate back';title.style.margin='0 0 8px';box.append(title);
 const list=document.createElement('div');list.style.cssText='overflow-y:auto;min-height:0;flex:1';const boxes=[];
 choices.forEach(item=>{const label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:10px;padding:10px 2px;border-bottom:1px solid #eee;font-size:16px';const cb=document.createElement('input');cb.type='checkbox';cb.checked=true;cb.style.cssText='width:20px;height:20px;flex:0 0 20px';const key=item.planId+'||'+weekdaySlotKey(item.day,item.cat);boxes.push({cb,key});const span=document.createElement('span');span.textContent=(mealPlans.length>1?item.planName+' · ':'')+item.day+' · '+item.cat+' — '+item.meal.name;label.append(cb,span);list.append(label)});box.append(list);
 const controls=document.createElement('div');controls.style.cssText='display:flex;gap:14px;align-items:center;margin-top:10px';
 const selectAll=document.createElement('button');selectAll.type='button';selectAll.textContent='Select all';selectAll.className='smallbtn';selectAll.onclick=()=>boxes.forEach(x=>x.cb.checked=true);
 const selectNone=document.createElement('button');selectNone.type='button';selectNone.textContent='Deselect all';selectNone.className='smallbtn';selectNone.onclick=()=>boxes.forEach(x=>x.cb.checked=false);
 const apply=document.createElement('button');apply.type='button';apply.textContent='Move selected';apply.className='smallbtn';apply.onclick=()=>{const chosen=boxes.filter(x=>x.cb.checked).map(x=>x.key);overlay.remove();rotateSelectedBack(chosen)};
 const cancel=document.createElement('button');cancel.type='button';cancel.textContent='Cancel';cancel.className='smallbtn';cancel.onclick=()=>overlay.remove();controls.append(selectAll,selectNone,apply,cancel);controls.style.flexWrap='wrap';box.append(controls);overlay.append(box);overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});document.body.append(overlay);
}
// Resolve a rotation against the whole resulting plan, not only earlier days.
// Reservations and temporary choices affect selection only; skipped recipes never
// leave their queue positions or acquire cooking/history changes.
function resolveRotatedMealSlots(plan, selected, retained){
 const slots=new Set(selected.map(item=>weekdaySlotKey(item.day,item.cat)));
 const reserved=new Map();
 for(const item of retained){if(!reserved.has(item.cat))reserved.set(item.cat,new Set());reserved.get(item.cat).add(String(item.meal.id))}
 function keepChoice(item){
  const key=weekdaySlotKey(item.day,item.cat),id=String(item.meal.id);
  plan.weekdayMealOverrides[key]=id;plan.cycleRetainedSlots[key]=id;
  plan.cycleSlotChoices[key]={...plan.cycleSlotChoices[key],mealId:id,parentId:String(item.linkedTo??'')};
 }
 let resolved=getDisplayedWeekdayMealsForPlan(plan,null,null,reserved);
 for(const item of resolved)if(slots.has(weekdaySlotKey(item.day,item.cat)))keepChoice(item);
 const tried=new Map();
 // Linked replacements take priority. Resolve any ordinary selected slot that
 // now conflicts with a retained meal, a linked replacement, or another new pick.
 // Each slot tries a recipe at most once, including cyclic linked definitions.
 while(true){
  resolved=getDisplayedWeekdayMealsForPlan(plan);
  const linked=item=>item.linkedTo!=null||resolved.some(parent=>parent!==item&&parent.day===item.day&&(parent.meal.linkedMealIds||[]).some(id=>String(id)===String(item.meal.id))&&!(plan.cycleSlotChoices[weekdaySlotKey(item.day,item.cat)]?.blockedParents||[]).some(id=>String(id)===String(parent.meal.id)));
  const fixed=resolved.filter(item=>!slots.has(weekdaySlotKey(item.day,item.cat))||linked(item));
  const used=new Map(),dependentUsed=new Set(fixed.map(item=>sharedRecipeIdentity(item.meal)));
  for(const item of fixed){if(!used.has(item.cat))used.set(item.cat,new Set());used.get(item.cat).add(String(item.meal.id))}
  let changed=false;
  for(const item of resolved){
   const key=weekdaySlotKey(item.day,item.cat);
   if(!slots.has(key)||linked(item))continue;
   const ids=used.get(item.cat)||new Set(),id=String(item.meal.id);
   if(ids.has(id)||(item.dependentSide&&dependentUsed.has(sharedRecipeIdentity(item.meal)))){
    if(!tried.has(key))tried.set(key,new Set());tried.get(key).add(id);
    const occupied=new Set(resolved.filter(other=>other!==item&&(item.dependentSide||other.cat===item.cat)).map(other=>item.dependentSide?sharedRecipeIdentity(other.meal):String(other.meal.id)));
    const next=automaticSlotCandidates(plan,item.day,item.cat,meals,resolved).find(meal=>!occupied.has(item.dependentSide?sharedRecipeIdentity(meal):String(meal.id))&&!tried.get(key).has(String(meal.id)));
    if(next){tried.get(key).add(String(next.id));keepChoice({day:item.day,cat:item.cat,meal:next});changed=true;break}
   }
   ids.add(id);used.set(item.cat,ids);if(item.dependentSide)dependentUsed.add(sharedRecipeIdentity(item.meal));
  }
  if(!changed)return;
 }
}
function moveDisplayedMealsToBottom(selectedSlots=null,allTabs=false,markCooked=false,retainedSlots=null,beforeState=null,preview=false){
 if(groceryCheckStorageInvalid){showAppMessage('Saved grocery check states could not be read. Export a backup before repairing this browser data.');return;}
 saveActiveMealPlan();
 const prior=new Map(mealPlans.map(plan=>[plan.id,rotationWeekEntries(plan)]));
 const scope=allTabs?mealPlans:mealPlans.filter(plan=>plan.id===activePlanId);
 // Explicit cycling advances manual substitutions too. Unchecked slots and
 // automatic queue changes retain their existing manual-choice protections.
 const selected=[];
 for(const plan of scope){
  for(const item of rotationSelectionEntries(plan)){
   const key=allTabs?plan.id+'||'+weekdaySlotKey(item.day,item.cat):weekdaySlotKey(item.day,item.cat);
   if(rotationSelectable(item,plan)&&(!selectedSlots||selectedSlots.has(key)))selected.push({...item,planId:plan.id});
  }
 }
 for(const plan of scope){const entries=prior.get(plan.id)||[],owners=selected.filter(item=>item.planId===plan.id);for(const item of entries)if(rotationSelectable(item,plan)&&owners.some(owner=>!owner.scheduleOnly&&owner.day===item.day&&pairedMainGroup(plan,item.day,item.cat)===owner.cat)&&!selected.some(other=>rotationOccurrenceKey(other)===rotationOccurrenceKey({...item,planId:plan.id})))selected.push({...item,planId:plan.id});}
 if(!selected.length)return;
 const hiddenRotated=[];for(const plan of scope){const base=queueWeekEntries(plan),keys=new Set(selected.filter(item=>item.planId===plan.id&&item.scheduleOnly).map(item=>temporarySlotKey(item.day,item.cat)));for(const entry of base)if(keys.has(temporaryGroceryOwner(plan,entry,base)))hiddenRotated.push({...entry,planId:plan.id,exact:true,scheduleOnly:true})}
 const rotationNow=new Date(),calendars=new Map();
 for(const plan of scope)if(selected.some(item=>item.planId===plan.id)){
  const calendar=rotationCalendarForPlan(plan,prior.get(plan.id)||[],rotationNow);calendars.set(plan.id,calendar);plan.rotationCalendar=calendar;
 }
 if(beforeState)beforeState={...beforeState,mealPlans:beforeState.mealPlans.map(plan=>calendars.has(plan.id)?{...plan,rotationCalendar:rotationCalendarForPlan(plan,getDisplayedWeekdayMealsForPlan(plan,null,beforeState),rotationNow)}:plan)};
 const selectedKeys=new Set(selected.map(rotationOccurrenceKey));
 const affected=[];const rotationOccurrences=[];
 for(const plan of mealPlans)for(const item of prior.get(plan.id)||[]){
  const occurrence={...item,planId:plan.id,planName:plan.name};
  rotationOccurrences.push({planId:plan.id,planName:plan.name,day:item.day,cat:item.cat,mealId:String(item.meal.id),parentId:String(item.linkedTo??''),scheduledSlot:rotationGroupScheduled(plan,item.day,item.cat),...(item.occasional?{occasional:true}:{}),...(item.scheduleOnly?{scheduleOnly:true}:{})});
  if(cycleAffectedEntries([occurrence],selected.filter(x=>x.planId===plan.id),plan).length)affected.push({...occurrence,exact:true});
 }
 // Capture the exact state before this rotation, including cross-tab meal overrides.
 // A manual move stages its destination first; keep its true pre-change Undo/Cycle Back state.
 const undoBefore=beforeState||JSON.parse(captureState()),{lastRotationBefore:oldRotationHistory,...rotationBefore}=undoBefore;
 const rotationRecord={...rotationBefore,cycledAt:rotationNow.toISOString(),rotationOccurrences:beforeState?beforeState.mealPlans.flatMap(plan=>rotationWeekEntries(plan,beforeState).map(item=>({planId:plan.id,planName:plan.name,day:item.day,cat:item.cat,mealId:String(item.meal.id),parentId:String(item.linkedTo??''),scheduledSlot:rotationGroupScheduled(plan,item.day,item.cat),...(item.occasional?{occasional:true}:{}),...(item.scheduleOnly?{scheduleOnly:true}:{})}))):rotationOccurrences,cookingCycledContexts:affected.concat(hiddenRotated).map(x=>({planId:x.planId,day:x.day,cat:x.cat,mealId:String(x.meal.id),parentId:String(x.linkedTo??''),exact:true}))};
 const linkedIds=new Set();
 for(const item of selected){const {meal,cat}=item,plan=mealPlans.find(p=>p.id===item.planId);if(!rotationAdvancesRecipe(item,plan,prior.get(plan.id)||[]))continue;if(dependentSideAutomatic(plan,item,prior.get(plan.id)||[])){linkedIds.add(String(meal.id));continue}
  if(meal.cat!==cat)continue;
  linkedIds.add(String(meal.id));
  if(meal.linkGroup)meals.filter(m=>m.linkGroup===meal.linkGroup).forEach(m=>linkedIds.add(String(m.id)));
 }
 for(const item of affected)if(item.meal.cat===item.cat&&rotationAdvancesRecipe(item,mealPlans.find(p=>p.id===item.planId),prior.get(item.planId)||[]))linkedIds.add(String(item.meal.id));
 const groceryBefore=captureGroceryCheckStates();
 const beforeIds=new Set(getDisplayedWeekdayMeals().map(({meal})=>String(meal.id)));
 if(!preview){snapshot(JSON.stringify(undoBefore));retainDueMakeAheadTasks()}
 rotationRecord.favoriteRotationTurns=[];for(const item of selected.filter(item=>rotationAdvancesRecipe(item,mealPlans.find(p=>p.id===item.planId),prior.get(item.planId)||[]))){const plan=mealPlans.find(p=>p.id===item.planId),source=dependentSideAutomatic(plan,item,prior.get(plan.id)||[])?item.meal.cat:item.cat,signature=plan&&advanceFavoriteRotation(plan,source,item.meal);if(signature)rotationRecord.favoriteRotationTurns.push({planId:plan.id,day:item.day,cat:source,slotCat:item.cat,mealId:String(item.meal.id),labels:[],signature})}

 for(const meal of meals)if(linkedIds.has(String(meal.id)))delete meal.rotationPromotionPriority;
 const byCategory={};
 for(const m of meals){
  if(m.rotation&&linkedIds.has(String(m.id))){
   if(!byCategory[m.cat])byCategory[m.cat]=[];
   byCategory[m.cat].push(m);
  }
 }
 for(const [cat,toMove] of Object.entries(byCategory)){
  const slots=[];
  meals.forEach((m,i)=>{if(m.cat===cat&&m.rotation)slots.push(i)});
  const current=slots.map(i=>meals[i]);
  const outgoing=new Set(toMove.map(m=>String(m.id)));
  const reordered=current.filter(m=>!outgoing.has(String(m.id))).concat(current.filter(m=>outgoing.has(String(m.id))));
  slots.forEach((slot,i)=>{meals[slot]=reordered[i]});
 }
 for(const plan of mealPlans){
  const overrides={...(plan.weekdayMealOverrides||{})},pins={...(plan.cycleRetainedSlots||{})},choices=JSON.parse(JSON.stringify(plan.cycleSlotChoices||{}));
  const entries=prior.get(plan.id)||[],planSelected=selected.filter(item=>item.planId===plan.id);
  for(const [key,choice]of Object.entries(choices))if((selectedSlots===null&&scope.includes(plan))||planSelected.some(item=>key.startsWith(item.day+'::'))){delete choice.excludedMealIds;delete choice.empty;}
  for(const item of entries){
   if(!rotationSelectable(item,plan)||item.scheduleOnly)continue;
   const {day,cat,meal}=item,key=weekdaySlotKey(day,cat),scopedKey=(allTabs?plan.id+'||':'')+key;
   const raw=plan.weekdayCategories?.[day],categories=Array.isArray(raw)?raw:[raw];
   if(categories[0]===cat)delete overrides[day];
   if(selectedKeys.has(rotationOccurrenceKey({...item,planId:plan.id}))){
    delete overrides[key];delete pins[key];
    const blocked=entries.filter(parent=>parent.day===day&&!planSelected.some(x=>x.day===day&&String(x.meal.id)===String(parent.meal.id))&&(parent.meal.linkedMealIds||[]).some(id=>{const target=meals.find(m=>String(m.id)===String(id));return target&&linkedRecipePlacement(plan,day,parent,target,entries)===cat})).map(parent=>String(parent.meal.id));
    choices[key]={parentId:'',avoidMealId:String(meal.id),...(pairedMainGroup(plan,day,cat)?{previousGroupId:groupIdentity(meal.cat)}:{}),blockedParents:[...new Set(blocked)]};
   }else{
    const old=choices[key],valid=old&&String(old.mealId)===String(meal.id),manual=manualWeekdayMealChoice(plan,day,cat,meal.id);
    const blocked=(valid?old.blockedParents||[]:[]).filter(id=>entries.some(parent=>parent.day===day&&String(parent.meal.id)===String(id))&&!planSelected.some(parent=>parent.day===day&&String(parent.meal.id)===String(id)));
    overrides[key]=String(meal.id);pins[key]=String(meal.id);
    choices[key]={...(valid?old:{}),...(manual?{substitution:true}:{}),mealId:String(meal.id),parentId:String(item.linkedTo??''),retain:manual||!!((allTabs||plan.id===activePlanId)&&retainedSlots?.has(scopedKey))||!!(valid&&old.retain),blockedParents:blocked};
   }
  }
  // A temporary empty/one-time slot can conceal a real queued recipe. When
  // it expires, release automatic pins; the hidden meal was not consumed, so
  // do not mark it as an outgoing recipe to avoid. Explicit manual choices stay.
  for(const hidden of hiddenRotated.filter(item=>item.planId===plan.id)){
   if(!rotationGroupScheduled(plan,hidden.day,hidden.cat))continue;
   const key=weekdaySlotKey(hidden.day,hidden.cat),old=choices[key];
   if(manualWeekdayMealChoice(plan,hidden.day,hidden.cat,hidden.meal.id))continue;
   delete overrides[key];delete pins[key];
   const assigned=plan.weekdayCategories?.[hidden.day];
   if((Array.isArray(assigned)?assigned:[assigned])[0]===hidden.cat)delete overrides[hidden.day];
   choices[key]={parentId:'',blockedParents:old?.blockedParents||[]};
  }
  for(const item of planSelected.filter(item=>item.emptyAssigned)){
   const key=weekdaySlotKey(item.day,item.cat);delete overrides[key];delete pins[key];
   const raw=plan.weekdayCategories?.[item.day];if((Array.isArray(raw)?raw:[raw])[0]===item.cat)delete overrides[item.day];
   choices[key]={parentId:'',blockedParents:choices[key]?.blockedParents||[]};
  }
  plan.weekdayMealOverrides=overrides;
  if(Object.keys(pins).length||plan.cycleRetainedSlots)plan.cycleRetainedSlots=pins;
  plan.cycleSlotChoices=choices;
 }
 for(const item of selected.filter(item=>item.scheduleOnly)){const plan=mealPlans.find(p=>p.id===item.planId);clearTemporarySlot(plan,item.day,item.cat)}
 // Reopen affected groups through automatic preferences, not hidden pins.
 // Include earlier unconsumed queue entries when old metadata identifies only
 // one deferred day. This also supports schedules saved before deferredMealIds.
 const outgoingIds=new Set(selected.filter(item=>!item.scheduleOnly).map(item=>String(item.meal.id)));
 const affectedKeys=new Set(affected.map(rotationOccurrenceKey));
 const fixedIds=new Set([...prior].flatMap(([planId,items])=>items.filter(item=>!item.scheduleOnly&&!affectedKeys.has(rotationOccurrenceKey({...item,planId}))).map(item=>String(item.meal.id))));
 // Unselected temporary slots also reserve their underlying selections. They
 // are absent from the visible prior list, but another tab must keep its turn.
 for(const oldPlan of rotationBefore.mealPlans){
  const base=getDisplayedWeekdayMealsForPlan(oldPlan,null,rotationBefore,null,true);
  for(const entry of base){
   const owner=temporaryGroceryOwner(oldPlan,entry,base);if(!owner)continue;
   const cycled=selected.some(item=>item.planId===oldPlan.id&&item.scheduleOnly&&temporarySlotKey(item.day,item.cat)===owner);
   const choice=oldPlan.cycleSlotChoices?.[weekdaySlotKey(entry.day,entry.cat)],deferred=choice?.deferredMealIds?.some(id=>String(id)!==String(entry.meal.id));
   if(!cycled||manualWeekdayMealChoice(oldPlan,entry.day,entry.cat,entry.meal.id)&&!deferred)fixedIds.add(String(entry.meal.id));
  }
 }
 for(const plan of scope){
  const oldPlan=rotationBefore.mealPlans.find(old=>old.id===plan.id),hidden=hiddenRotated.filter(item=>item.planId===plan.id),hiddenSet=new Set(hidden);
  const reopening=selected.filter(item=>item.planId===plan.id&&!item.scheduleOnly).concat(hidden).sort((a,b)=>orderedDays().indexOf(a.day)-orderedDays().indexOf(b.day));
  const due=new Map(),groups=new Set(),manualHidden=new Set(),reset=new Set();
  const hiddenGroups=new Set(hidden.filter(item=>rotationGroupScheduled(plan,item.day,item.cat)).map(item=>item.cat));
  for(const item of reopening){
   if(!rotationGroupScheduled(plan,item.day,item.cat))continue;
   const key=weekdaySlotKey(item.day,item.cat),old=oldPlan?.cycleSlotChoices?.[key];
   const raw=old?.deferredMealIds?.length?old.deferredMealIds:old?.skipReplacement&&old.avoidMealId?[old.avoidMealId]:[];
   const ids=raw.map(String).filter(id=>id!==String(item.meal.id)&&!linkedIds.has(id));
   if(hiddenSet.has(item)&&manualWeekdayMealChoice(oldPlan,item.day,item.cat,item.meal.id)&&!ids.length){manualHidden.add(key);fixedIds.add(String(item.meal.id));continue;}
   if(raw.length)reset.add(key);
   if(hiddenSet.has(item)||raw.length)groups.add(item.cat);
   if(!due.has(item.cat))due.set(item.cat,[]);
   for(const id of ids)if(!due.get(item.cat).includes(id))due.get(item.cat).push(id);
  }
  const rank=new Map(rotationBefore.meals.map((meal,index)=>[String(meal.id),index])),pending=new Map(),assigned=new Map();
  for(const cat of groups){
   const held=(due.get(cat)||[]).sort((a,b)=>(rank.get(a)??Infinity)-(rank.get(b)??Infinity));
   if(!hiddenGroups.has(cat)){pending.set(cat,held);continue;}
   const first=reopening.find(item=>item.cat===cat&&!manualHidden.has(weekdaySlotKey(item.day,item.cat))),old=first&&oldPlan?.cycleSlotChoices?.[weekdaySlotKey(first.day,cat)];
   const firstHeld=old?.deferredMealIds?.some(id=>String(id)!==String(first.meal.id))||old?.skipReplacement&&old.avoidMealId&&String(old.avoidMealId)!==String(first.meal.id);
   const queue=automaticRecipeCandidates(cat,[],meals,plan).map(meal=>String(meal.id)),end=Math.max(-1,...held.map(id=>queue.indexOf(id)));
   const ids=firstHeld?held:queue.slice(0,end+1);
   pending.set(cat,ids.filter(id=>!outgoingIds.has(id)&&!fixedIds.has(id)));
   assigned.set(cat,new Set());
  }
  for(const item of reopening){
   const key=weekdaySlotKey(item.day,item.cat);if(!groups.has(item.cat)||manualHidden.has(key)||!rotationGroupScheduled(plan,item.day,item.cat))continue;
   // No temporary slot in this group: retain the established rotation behavior.
   if(!hiddenGroups.has(item.cat)){
    const ids=pending.get(item.cat);if(!ids.length&&!reset.has(key))continue;
    delete plan.weekdayMealOverrides[key];delete plan.cycleRetainedSlots[key];
    const raw=plan.weekdayCategories?.[item.day],categories=Array.isArray(raw)?raw:[raw];if(categories[0]===item.cat)delete plan.weekdayMealOverrides[item.day];
    plan.cycleSlotChoices[key]={parentId:'',avoidMealId:String(item.meal.id),blockedParents:plan.cycleSlotChoices[key]?.blockedParents||[]};
    const possible=automaticSlotCandidates(plan,item.day,item.cat),next=ids.map(id=>possible.find(meal=>String(meal.id)===id)).find(Boolean);
    if(next){const id=String(next.id);ids.splice(ids.indexOf(id),1);plan.weekdayMealOverrides[key]=id;plan.cycleRetainedSlots[key]=id;plan.cycleSlotChoices[key].mealId=id;}
    continue;
   }
   delete plan.weekdayMealOverrides[key];delete plan.cycleRetainedSlots[key];
   const raw=plan.weekdayCategories?.[item.day],categories=Array.isArray(raw)?raw:[raw];if(categories[0]===item.cat)delete plan.weekdayMealOverrides[item.day];
   plan.cycleSlotChoices[key]={parentId:'',blockedParents:plan.cycleSlotChoices[key]?.blockedParents||[],...(!hiddenSet.has(item)?{avoidMealId:String(item.meal.id)}:{})};
   const possible=automaticSlotCandidates(plan,item.day,item.cat),used=assigned.get(item.cat),available=possible.filter(meal=>!used.has(String(meal.id))&&!fixedIds.has(String(meal.id)));
   const ids=pending.get(item.cat),next=ids.map(id=>available.find(meal=>String(meal.id)===id)).find(Boolean)||available.find(meal=>!outgoingIds.has(String(meal.id)))||available[0];
   if(next){const id=String(next.id);used.add(id);if(ids.includes(id))ids.splice(ids.indexOf(id),1);plan.weekdayMealOverrides[key]=id;plan.cycleRetainedSlots[key]=id;plan.cycleSlotChoices[key].mealId=id;}
  }
 }
 for(const plan of scope){const entries=prior.get(plan.id)||[];rememberDependentSideState(plan,entries);for(const day of weekdays){const raw=plan.weekdayCategories?.[day];for(const cat of Array.isArray(raw)?raw:[raw]){if(!cat)continue;const parent=pairedMainGroup(plan,day,cat);if(!parent)continue;const owner=selected.some(item=>!item.scheduleOnly&&item.planId===plan.id&&item.day===day&&item.cat===parent),side=selected.some(item=>!item.scheduleOnly&&item.planId===plan.id&&item.day===day&&item.cat===cat);if(!owner&&!side)continue;const key=dependentSideKey(day,cat),old=plan.dependentSideState[key];plan.dependentSideState[key]={...old,...(owner?{mainId:'__rotating__'}:{}),mealId:'',automatic:false};if(owner&&!entries.some(item=>item.day===day&&item.cat===cat)){delete plan.cycleSlotChoices?.[weekdaySlotKey(day,cat)];delete plan.weekdayMealOverrides?.[weekdaySlotKey(day,cat)];delete plan.cycleRetainedSlots?.[weekdaySlotKey(day,cat)]}}}}
 const resolvingActive=mealPlans.find(plan=>plan.id===activePlanId);weekdayMealOverrides={...(resolvingActive?.weekdayMealOverrides||{})};
 // Resolve selected slots through the existing linked-priority planner. Retained
 // parents are suppressed only in explicitly rotated groups; new mains may link in.
 for(const plan of mealPlans){
  const planSelected=selected.filter(item=>item.planId===plan.id&&!item.scheduleOnly);
  if(!planSelected.length)continue;
  plan.cycleRetainedSlots={...(plan.cycleRetainedSlots||{})};
  const retained=(prior.get(plan.id)||[]).filter(item=>!affected.some(outgoing=>outgoing.planId===plan.id&&rotationOccurrenceKey(outgoing)===rotationOccurrenceKey({...item,planId:plan.id})));
  resolveRotatedMealSlots(plan,planSelected,retained);
  const resolved=getDisplayedWeekdayMealsForPlan(plan);for(const item of planSelected)if(pairedMainGroup(plan,item.day,item.cat)&&sideServeWith(plan,item.day,item.cat,resolved).length&&!resolved.some(now=>now.day===item.day&&now.cat===item.cat)){const key=weekdaySlotKey(item.day,item.cat);plan.cycleSlotChoices[key]={...plan.cycleSlotChoices[key],empty:true,sideUnavailable:true};}
 }
 const activePlan=mealPlans.find(plan=>plan.id===activePlanId);
 weekdayMealOverrides={...(activePlan?.weekdayMealOverrides||{})};
 const rotatedOut=affected.filter(item=>!item.scheduleOnly&&!getDisplayedWeekdayMealsForPlan(mealPlans.find(plan=>plan.id===item.planId)).some(next=>next.day===item.day&&next.cat===item.cat&&String(next.meal.id)===String(item.meal.id)));
 const cookedResult=markCooked?recordRotatedMealsCooked(rotatedOut,calendars,rotationNow):{updates:[],skipped:[]};rotationRecord.cookedDateUpdates=cookedResult.updates;
 advanceRotationCalendars(calendars,affected,rotationNow,selectedSlots===null);
 if(preview)return;
 saveWeekdayMealOverrides();
 clearCycledCookingContexts(affected.concat(hiddenRotated));
 reconcileRotatedGroceryChecks(groceryBefore,affected.concat(hiddenRotated));
 resetGroceriesForNewTopMeals(beforeIds);
 topIngredientExpanded.clear();topIngredientManualHiddenOverride.clear();
 try{localStorage.setItem(ROTATION_BACK_KEY,JSON.stringify(rotationRecord))}catch(e){}
 persist();renderTabs();renderList();
}
// Cooking history is stored on the meal itself so existing data exports include it.
function appendLastCookedLabel(parent,meal){
 const label=lastCookedLabel(meal);if(!showLastCooked||!label)return;
 const date=document.createElement('div');date.className='meal-last-cooked';date.textContent=label;
 date.title='Tap to edit last cooked date';date.setAttribute('role','button');date.tabIndex=0;
 date.onclick=e=>{e.stopPropagation();editMealCookedDate(meal)};
 date.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();editMealCookedDate(meal)}};
 parent.append(date);
}
function lastCookedLabel(meal){
 if(!meal.lastCooked)return '';
 const date=new Date(meal.lastCooked);
 return Number.isNaN(date.getTime())?'':'Last cooked '+date.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'});
}
// Scheduled local dates are assigned when an occurrence is created, never inferred
// from the day it is cycled or from a number of rotations. V1 dates were guesses.
const cookingWeekdays=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
function cookingLocalDate(date){return date.getFullYear()+'-'+String(date.getMonth()+1).padStart(2,'0')+'-'+String(date.getDate()).padStart(2,'0')}
function parseCookingLocalDate(value){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return null;
 const date=new Date(value+'T12:00:00');return !Number.isNaN(date.getTime())&&cookingLocalDate(date)===value?date:null;
}
function cookingPlanningWeekStart(now=new Date()){
 const date=new Date(now),start=cookingWeekdays.indexOf(startWeekday);date.setHours(12,0,0,0);
 date.setDate(date.getDate()-(date.getDay()-(start<0?1:start)+7)%7);return date;
}
function cookingDateInWeek(day,start){
 const target=cookingWeekdays.indexOf(day);if(target<0||!start)return null;
 const date=new Date(start);date.setDate(date.getDate()+(target-start.getDay()+7)%7);return date;
}
function nextScheduledCookingDate(day,now,week=null,prior=null){
 let date=cookingDateInWeek(day,week||cookingPlanningWeekStart(now));if(!date)return null;
 while(cookingLocalDate(date)<cookingLocalDate(now))date.setDate(date.getDate()+7);
 const saved=parseCookingLocalDate(prior);if(saved&&saved>date)date=saved;
 return cookingLocalDate(date);
}
function rotationCalendarSlot(item){return weekdaySlotKey(item.day,item.cat)+(item.occasional?'::one-time':'::slot')}
function rotationCalendarForPlan(plan,entries,now=new Date()){
 const saved=plan.rotationCalendar,dated=saved?.version===2,occurrences={},assignedOn={},assignedAt={},slots={};
 const canAssign=!restoringRotationCalendars&&dated;
 for(const item of entries){
  const key=rotationOccurrenceKey({...item,planId:plan.id}),stored=dated?parseCookingLocalDate(saved.occurrences?.[key]):null;
  const on=dated?parseCookingLocalDate(saved.assignedOn?.[key]):null;
  let date=stored&&on&&on<=stored&&cookingWeekdays[stored.getDay()]===item.day?cookingLocalDate(stored):null;
  const known=dated&&Object.prototype.hasOwnProperty.call(saved.occurrences||{},key);
  if(!known&&canAssign)date=nextScheduledCookingDate(item.day,now,null,saved?.slots?.[rotationCalendarSlot(item)]);
  occurrences[key]=date;assignedOn[key]=known?saved.assignedOn?.[key]||null:date?cookingLocalDate(now):null;assignedAt[key]=known?saved.assignedAt?.[key]||null:date?now.toISOString():null;
 }
 // A linked-only attachment has its parent's scheduled date, not a separate week.
 for(const item of entries)if(item.linkedTo!=null&&!rotationGroupScheduled(plan,item.day,item.cat)){
  const parent=entries.find(parent=>parent.day===item.day&&String(parent.meal.id)===String(item.linkedTo));if(!parent)continue;
  const key=rotationOccurrenceKey({...item,planId:plan.id}),owner=rotationOccurrenceKey({...parent,planId:plan.id});
  occurrences[key]=occurrences[owner];assignedOn[key]=assignedOn[owner];assignedAt[key]=assignedAt[owner];
 }
 const weeks=[];
 for(const item of entries){const key=rotationOccurrenceKey({...item,planId:plan.id}),date=occurrences[key];slots[rotationCalendarSlot(item)]=date;if(date&&rotationSelectable(item,plan))weeks.push(cookingLocalDate(cookingPlanningWeekStart(parseCookingLocalDate(date))))}
 const calendar={version:2,weekStart:weeks.length?weeks.sort()[0]:null,occurrences,assignedOn,assignedAt,slots};
 if(dated&&saved.legacyCalendar)calendar.legacyCalendar=saved.legacyCalendar;
 else if(saved&&!dated)calendar.legacyCalendar=JSON.parse(JSON.stringify(saved));
 return calendar;
}
function scheduledCalendarEntries(plan){
 const visible=showMealPlanTabs,entries=new Map();
 try{for(const mode of [true,false]){
  showMealPlanTabs=mode;const current=plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan;
  for(const item of getDisplayedWeekdayMealsForPlan(current))entries.set(rotationOccurrenceKey({...item,planId:plan.id}),item);
 }}finally{showMealPlanTabs=visible}
 return [...entries.values()];
}
function reconcileRotationCalendars(){
 if(!rotationCalendarTrackingReady)return;
 let changed=stabilizeAutomaticWeekSlots();const now=new Date();
 for(const plan of mealPlans){
  const calendar=rotationCalendarForPlan(plan,scheduledCalendarEntries(plan),now);
  if(JSON.stringify(plan.rotationCalendar)!==JSON.stringify(calendar)){plan.rotationCalendar=calendar;changed=true}
 }
 if(changed)try{localStorage.setItem(mealPlansKey,JSON.stringify({plans:mealPlans,activeId:activePlanId}))}catch(e){}
}
function cookedDateForWeekday(day,weekStart=null,now=new Date()){
 const date=cookingDateInWeek(day,parseCookingLocalDate(weekStart));return date&&cookingLocalDate(date)<=cookingLocalDate(now)?date:null;
}
function outgoingOccurrenceDate(item,calendar=null,now=new Date()){
 const explicit=parseCookingLocalDate(cookingSession(cookingContext(item.planId,item.day,item.cat,item.meal,item.linkedTo??item.parentId))?.cookedDate);
 if(explicit)return explicit;
 return scheduledOccurrenceDate(item,calendar,now);
}
function scheduledOccurrenceDate(item,calendar=null,now=new Date()){
 const key=rotationOccurrenceKey(item),stored=parseCookingLocalDate(calendar?.occurrences?.[key]);if(stored)return stored;
 const legacy=calendar?.legacyCalendar||calendar;
 return cookingDateInWeek(item.day,parseCookingLocalDate(legacy?.weekStart)||cookingPlanningWeekStart(now));
}
function recordRotatedMealsCooked(selected,calendars=new Map(),now=new Date()){
 const groups=new Map(),skipped=[],identity=meal=>meal.linkGroup?'linked:'+meal.linkGroup:'meal:'+meal.id;
 for(const item of selected){
  const key=rotationOccurrenceKey(item),date=outgoingOccurrenceDate(item,calendars.get(item.planId),now);
  if(!date||cookingLocalDate(date)>cookingLocalDate(now)){skipped.push(item.meal.name||'Untitled meal');continue}
  const id=identity(item.meal);if(!groups.has(id))groups.set(id,[]);groups.get(id).push({key,date:cookingLocalDate(date)});
 }
 const updates=[];
 for(const meal of meals){
  const events=groups.get(identity(meal));if(!events?.length)continue;
  const date=parseCookingLocalDate(events.map(event=>event.date).sort().at(-1)),existing=meal.lastCooked?new Date(meal.lastCooked):null;
  if(!existing||Number.isNaN(existing.getTime())||date>existing){const before=meal.lastCooked??null,after=date.toISOString();meal.lastCooked=after;updates.push({mealId:String(meal.id),before,after,events})}
 }
 return {updates,skipped:[...new Set(skipped)]};
}
function advanceRotationCalendars(calendars,affected,now,wholeWeek=false){
 for(const plan of mealPlans){
  const before=calendars.get(plan.id);if(!before)continue;
  const entries=getDisplayedWeekdayMealsForPlan(plan),outgoing=new Set(affected.filter(item=>item.planId===plan.id).map(rotationOccurrenceKey));
  let incomingWeek=null;
  if(wholeWeek){
   const current=cookingPlanningWeekStart(now),old=parseCookingLocalDate(before.weekStart);
   if(old){old.setDate(old.getDate()+7);incomingWeek=old>current?old:current}
   else{incomingWeek=current;if(cookingLocalDate(incomingWeek)<cookingLocalDate(now))incomingWeek.setDate(incomingWeek.getDate()+7)}
  }
  const calendar={...before,occurrences:{},assignedOn:{},assignedAt:{},slots:{}};
  for(const item of entries){
   const key=rotationOccurrenceKey({...item,planId:plan.id}),known=Object.prototype.hasOwnProperty.call(before.occurrences||{},key);
   if(known&&!outgoing.has(key)){calendar.occurrences[key]=before.occurrences[key];calendar.assignedOn[key]=before.assignedOn[key];calendar.assignedAt[key]=before.assignedAt[key]}
   else{calendar.occurrences[key]=nextScheduledCookingDate(item.day,now,incomingWeek,before.occurrences?.[key]);calendar.assignedOn[key]=cookingLocalDate(now);calendar.assignedAt[key]=now.toISOString()}
  }
  plan.rotationCalendar=calendar;plan.rotationCalendar=rotationCalendarForPlan(plan,entries,now);
 }
}
function restoreRotationCalendarSlots(previous,desired){
 const wasRestoring=restoringRotationCalendars;restoringRotationCalendars=true;
 try{for(const plan of mealPlans){
  const selected=desired.filter(item=>item.planId===plan.id);if(!selected.length)continue;
  const old=previous.mealPlans.find(old=>old.id===plan.id);if(!old)continue;
  const prior=rotationCalendarForPlan(old,getDisplayedWeekdayMealsForPlan(old,null,previous));
  const entries=getDisplayedWeekdayMealsForPlan(plan),current=rotationCalendarForPlan(plan,entries);
  for(const item of cycleAffectedEntries(entries.map(item=>({...item,planId:plan.id})),selected,plan)){
   const key=rotationOccurrenceKey(item);current.occurrences[key]=prior.occurrences[key]??null;current.assignedOn[key]=prior.assignedOn[key]??null;current.assignedAt[key]=prior.assignedAt[key]??null;
  }
  plan.rotationCalendar=current;plan.rotationCalendar=rotationCalendarForPlan(plan,entries);
 }}finally{restoringRotationCalendars=wasRestoring}
}
function restoredRotationCookedDates(previous,keys=null){
 const result=new Map(),updates=Array.isArray(previous.cookedDateUpdates)?previous.cookedDateUpdates:[];
 for(const meal of meals){
  const update=updates.find(update=>update.mealId===String(meal.id));let value=meal.lastCooked??null;
  if(update&&value===update.after){
   const remaining=keys?(update.events||[]).filter(event=>!keys.has(event.key)):[];
   value=update.before;for(const event of remaining){const date=parseCookingLocalDate(event.date),prior=value?new Date(value):null;if(date&&(!prior||Number.isNaN(prior.getTime())||date>prior))value=date.toISOString()}
  }
  result.set(String(meal.id),value);
 }
 return result;
}
function applyRestoredCookedDates(records,dates){for(const meal of records)if(dates.has(String(meal.id))){const value=dates.get(String(meal.id));if(value===null)delete meal.lastCooked;else meal.lastCooked=value}}
function editMealCookedDate(meal,onChanged=null,context=null){
 const d=recipeBulkDialog('Edit last cooked date'),overlay=d.overlay,panel=d.panel;
 const name=document.createElement('div');name.textContent=meal.name||'Meal';name.style.marginBottom='12px';panel.append(name);
 const field=document.createElement('input');field.type='date';field.setAttribute('aria-label','Choose last cooked date');
 field.style.cssText='width:100%;min-width:0;min-height:44px;border:0;background:transparent;color:inherit;font-size:16px';
 if(meal.lastCooked){const d=new Date(meal.lastCooked);if(!Number.isNaN(d.getTime())){const local=new Date(d.getTime()-d.getTimezoneOffset()*60000);field.value=local.toISOString().slice(0,10)}}
 const dateWrap=document.createElement('div');dateWrap.style.cssText='position:relative;border:1px solid #aaa;border-radius:9px;padding:13px 14px;display:flex;align-items:center;justify-content:space-between;min-height:52px';
 const dateText=document.createElement('span');dateText.hidden=true;
 const showDate=()=>{dateText.textContent=field.value?new Date(field.value+'T12:00:00').toLocaleDateString(undefined,{month:'long',day:'numeric',year:'numeric'}):'Select a date'};
 showDate();field.addEventListener('change',showDate);
 dateWrap.append(dateText);const calendarIcon=document.createElement('span');calendarIcon.innerHTML='<svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 2v6M17 2v6M3 10h18"/></svg>';dateWrap.append(calendarIcon,field);
 dateWrap.onclick=event=>{if(event.target===field)return;try{field.showPicker()}catch(e){field.focus()}};panel.append(dateWrap);
 const actions=document.createElement('div');actions.className='meal-unified-actions';actions.style.marginTop='10px';
 const button=(label,type,fn)=>{const el=document.createElement('button');el.type='button';setIconButton(el,type,label);el.style.width='52px';el.style.height='48px';el.onclick=fn;actions.append(el)};
 button('Save','save',()=>{if(!field.value)return;const date=new Date(field.value+'T12:00:00');if(Number.isNaN(date.getTime()))return;snapshot();for(const m of meals)if(m.id===meal.id||(meal.linkGroup&&m.linkGroup===meal.linkGroup))m.lastCooked=date.toISOString();if(context){cookingSession(context,true);const next=JSON.parse(JSON.stringify(cookingSessions));next.occurrences[cookingOccurrenceKey(context)].cookedDate=field.value;writeCookingSessions(next)}persist();d.close();renderList();onChanged?.()});
 button('Clear date','delete',async()=>{if(await appDialog('Are you sure you want to delete '+(meal.lastCooked?lastCookedLabel(meal).replace(/^Last cooked /,''):'this date')+'?',null,'yesno')!==true)return;snapshot();for(const m of meals)if(m.id===meal.id||(meal.linkGroup&&m.linkGroup===meal.linkGroup))delete m.lastCooked;if(context&&cookingSession(context)){const next=JSON.parse(JSON.stringify(cookingSessions));delete next.occurrences[cookingOccurrenceKey(context)].cookedDate;writeCookingSessions(next)}persist();d.close();renderList();onChanged?.()});
 button('Cancel','cancel',()=>d.close()); panel.append(actions);overlay.append(panel);
 overlay.addEventListener('click',e=>{if(e.target===overlay)d.close()});
 overlay.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();d.close()}});
 document.body.append(overlay);
}
// Rotate-out menu: keep the cooking-date choice between uses.
const ROTATE_MARK_COOKED_KEY='mealRotationMarkRotatedCookedV1';
function openRotateOptions(allTabs=false){
 const overlay=document.createElement('div');
 overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:10002;display:flex;align-items:center;justify-content:center;padding:18px';
 const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Rotate out recipes');
 panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:22px;width:100%;max-width:480px;box-shadow:0 12px 36px #0003';
 appendRotationCloseHeader(panel,'Rotate out recipes',()=>overlay.remove());
 const label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:10px;margin-bottom:18px;font-size:16px';
 const check=document.createElement('input');check.type='checkbox';check.checked=(localStorage.getItem(ROTATE_MARK_COOKED_KEY)??localStorage.getItem('mealRotationMarkRotatedAsCookedV1'))==='true';check.style.cssText='width:21px;height:21px;flex:none';
 check.onchange=()=>{try{localStorage.setItem(ROTATE_MARK_COOKED_KEY,String(check.checked))}catch(e){}};
 label.append(check,document.createTextNode('Mark rotated recipes as cooked'));panel.append(label);
 const actions=document.createElement('div');actions.style.cssText='display:flex;flex-direction:column;gap:12px';
 function option(text,fn){const b=document.createElement('button');b.type='button';b.className='smallbtn';b.textContent=text;b.style.cssText='padding:12px 14px;width:100%;font-size:16px';b.onclick=()=>{const mark=check.checked;overlay.remove();fn(mark)};actions.append(b)}
 option('Rotate out all recipes',mark=>moveDisplayedMealsToBottom(null,allTabs,mark));
 option('Select recipes to rotate out',mark=>openMoveMealChooser(allTabs,mark));
 panel.append(actions);overlay.append(panel);overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});
 overlay.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();overlay.remove()}});document.body.append(overlay);
}
function openMoveMealChooser(allTabs=false,markCooked=false){
 const shown=(allTabs?(saveActiveMealPlan(),mealPlans.flatMap(plan=>rotationSelectionEntries(plan).map(x=>({...x,planId:plan.id,planName:plan.name})))):rotationSelectionEntries({...mealPlans.find(p=>p.id===activePlanId),weekdayCategories,weekdayMealOverrides})).filter(item=>rotationSelectable(item,mealPlans.find(plan=>plan.id===(item.planId??activePlanId))));
 if(!shown.length)return;const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:10002;display:flex;align-items:center;justify-content:center;padding:16px';const box=document.createElement('div');box.style.cssText='background:white;color:#222;border-radius:14px;padding:18px 18px 12px;max-width:520px;width:100%;max-height:82vh;overflow:hidden;display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-rows:auto minmax(0,1fr) auto;gap:10px 8px;box-shadow:0 8px 30px #0004';const title=document.createElement('h3');title.textContent='Select meals to rotate out';title.style.cssText='margin:0;min-width:0;align-self:center;overflow-wrap:break-word;grid-column:1;grid-row:1';const hint=document.createElement('p');hint.textContent='Select the meals you want to advance. Unselected meals will stay where they are.';hint.style.cssText='font-size:14px;color:#666;margin:0 0 10px';const list=document.createElement('div');list.style.cssText='overflow-y:auto;min-height:0;grid-column:1/-1;grid-row:2';const boxes=[];shown.forEach(({day,cat,meal,planId,planName})=>{const label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:10px;padding:10px 2px;border-bottom:1px solid #eee;font-size:16px';const cb=document.createElement('input');cb.type='checkbox';cb.checked=true;cb.setAttribute('aria-label',(allTabs?planName+' · ':'')+day+' · '+cat+' — '+(meal.name==='—'||meal.id.toString().startsWith('empty:')?'—':meal.name));cb.style.cssText='width:20px;height:20px;flex:0 0 20px';boxes.push({day,cat,planId,cb});const text=document.createElement('span');text.style.cssText='display:flex;flex-direction:column;gap:4px;min-width:0';const weekday=document.createElement('span');weekday.className='section';weekday.style.cssText='margin:0;font-size:12px;letter-spacing:.09em;color:#777';weekday.textContent=day.slice(0,3).toUpperCase();const recipeName=document.createElement('span');recipeName.textContent=meal.id.toString().startsWith('empty:')?'—':meal.name;text.append(weekday,recipeName);const tint=colorForDay(day);label.style.background=tint;label.style.borderRadius='8px';label.style.padding='10px 8px';label.style.marginBottom='5px';label.append(cb,text);list.append(label)});const selectRow=document.createElement('div');selectRow.style.cssText='display:flex;align-items:center;gap:4px;grid-column:2;grid-row:1;align-self:start';const selectAll=document.createElement('button');selectAll.type='button';selectAll.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="m7 12 3 3 7-7"/></svg>';selectAll.title='Select all';selectAll.setAttribute('aria-label','Select all');selectAll.style.cssText='border:0;background:transparent;color:#555;padding:5px;min-width:44px;min-height:44px;display:flex;align-items:center;justify-content:center';selectAll.onclick=()=>boxes.forEach(x=>x.cb.checked=true);const selectNone=document.createElement('button');selectNone.type='button';selectNone.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 12h8"/></svg>';selectNone.title='Deselect all';selectNone.setAttribute('aria-label','Deselect all');selectNone.style.cssText='border:0;background:transparent;color:#555;padding:5px;min-width:44px;min-height:44px;display:flex;align-items:center;justify-content:center';selectNone.onclick=()=>boxes.forEach(x=>x.cb.checked=false);selectRow.append(selectAll,selectNone);const actions=document.createElement('div');actions.style.cssText='display:flex;justify-content:space-between;align-items:center;gap:14px;grid-column:1/-1;grid-row:3';const apply=document.createElement('button');apply.type='button';apply.textContent='Move selected';apply.style.cssText='flex:1;padding:10px;border:1px solid #ccc;border-radius:8px;background:#e8eefb;color:#222';apply.onclick=()=>{const slots=new Set(boxes.filter(x=>x.cb.checked).map(x=>(allTabs?x.planId+'||':'')+weekdaySlotKey(x.day,x.cat)));overlay.remove();if(slots.size)moveDisplayedMealsToBottom(slots,allTabs,markCooked,new Set(boxes.filter(x=>!x.cb.checked).map(x=>(allTabs?x.planId+'||':'')+weekdaySlotKey(x.day,x.cat))))};const cancel=document.createElement('button');cancel.type='button';cancel.textContent='Cancel';cancel.style.cssText='flex:1;padding:10px;border:1px solid #ccc;border-radius:8px;background:white;color:#222';cancel.onclick=()=>overlay.remove();setIconButton(apply,'save','Move selected');setIconButton(cancel,'cancel','Cancel');apply.style.minWidth=cancel.style.minWidth='44px';apply.style.minHeight=cancel.style.minHeight='44px';actions.append(apply,cancel);box.append(title,selectRow,list,actions);overlay.append(box);overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});document.body.append(overlay)}
// Swipe right opens a choice rather than deleting the meal immediately.
function openMealSwipeMenu(meal){
 if(!meals.some(item=>item.id===meal.id))return;
 const shade=document.createElement('div');shade.id='mealSwipeMenu';
 shade.style.cssText='position:fixed;inset:0;z-index:15000;background:#0008;display:flex;align-items:center;justify-content:center;padding:16px';
 const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');
 panel.setAttribute('aria-labelledby','mealSwipeMenuHeading');
 panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:22px;width:100%;max-width:460px;box-shadow:0 12px 36px #0003';
 const top=document.createElement('div');top.style.cssText='display:flex;align-items:start;justify-content:space-between;gap:12px;margin-bottom:20px';
 const heading=document.createElement('strong');heading.id='mealSwipeMenuHeading';heading.textContent=meal.name||'Untitled meal';heading.style.cssText='font-size:19px;line-height:1.3';
 const dismiss=document.createElement('button');dismiss.type='button';setIconButton(dismiss,'cancel','Cancel');
 dismiss.onclick=()=>shade.remove();top.append(heading,dismiss);panel.append(top);
 const buttons=document.createElement('div');buttons.style.cssText='display:flex;flex-direction:column;gap:12px';
 function option(label,action){const b=document.createElement('button');b.type='button';b.className='smallbtn';b.textContent=label;b.style.cssText='width:100%;min-height:48px;padding:10px 14px;text-align:center;font-size:16px';b.onclick=()=>{shade.remove();action()};buttons.append(b);return b}
 const shared=sharedRecipeMembers(meal).length>1,hint=document.createElement('p');hint.textContent=shared?'Removing this recipe from this group keeps it in its other groups. The group itself is not deleted.':'Deleting this recipe removes it from the recipe collection and its scheduled slots.';hint.style.cssText='font-size:14px;color:#666';panel.append(hint);
 option(shared?'Remove from this group':'Delete recipe',()=>{
  if(!meals.some(item=>item.id===meal.id))return;
  try{applyRecipeBulk([String(meal.id)],{delete:true});if(editId===meal.id)editId=null}
  catch(error){showAppMessage('Recipe could not be deleted: '+error.message)}
 });
 if(meal.cat)option(meal.rotation?'Remove from rotation':'Move to rotation',()=>{
  const current=meals.find(item=>item.id===meal.id);if(!current)return;
  if(!current.rotation){promoteMealToRotation(current);return}
  demoteMealToIdeas(current);
 });
 panel.append(buttons);shade.append(panel);shade.onclick=e=>{if(e.target===shade)shade.remove()};
 shade.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();shade.remove()}});
 document.body.append(shade);
}
function bindMealSwipe(row,m){let startX=0,startY=0,tracking=false,swipedAt=0,touchStart=null;function finish(dx,dy,e){if(row.classList.contains('meal-card-edit-mode'))return false;if(Math.abs(dx)<55||Math.abs(dx)<Math.abs(dy)*1.2)return false;swipedAt=Date.now();if(e&&e.cancelable)e.preventDefault();if(e)e.stopPropagation();if(dx<0){openEditor(m.id)}else{openMealSwipeMenu(m)}return true}row.addEventListener('touchstart',e=>{touchStart=null;if(row.classList.contains('meal-card-edit-mode'))return;if(recipeBulkMode||e.target.closest('.move,.check,.recipe-section-move,.needs-tweaking-icon,.recipe-list-timer,.recipe-personal-icon,.week-reorder-handle'))return;const t=e.touches[0];if(t)touchStart={x:t.clientX,y:t.clientY}},{passive:true});row.addEventListener('touchend',e=>{if(!touchStart)return;const t=e.changedTouches[0],start=touchStart;touchStart=null;if(t)finish(t.clientX-start.x,t.clientY-start.y,e)},{passive:false});row.addEventListener('touchcancel',()=>{touchStart=null});row.addEventListener('pointerdown',e=>{if(row.classList.contains('meal-card-edit-mode'))return;if(e.pointerType!=='mouse')return;if(recipeBulkMode||e.button!==0||e.target.closest('.move,.check,.recipe-section-move,.needs-tweaking-icon,.recipe-list-timer,.recipe-personal-icon,.week-reorder-handle'))return;startX=e.clientX;startY=e.clientY;tracking=true});row.addEventListener('pointerup',e=>{if(!tracking)return;tracking=false;finish(e.clientX-startX,e.clientY-startY,e)},{passive:false});row.addEventListener('pointercancel',()=>{tracking=false});row.addEventListener('click',e=>{if(row.classList.contains('meal-card-edit-mode'))return;if(Date.now()-swipedAt<700){e.preventDefault();e.stopPropagation();swipedAt=0}},true)}
// My Rotation uses the single Settings button in the main toolbar.
// Keep these callers as no-ops so other view toolbars remain unchanged.
function appendMealPlanSettingsGear(topControls){}
function appendMealPlanSettingsPanel(list){}
function placeViewToolbar(controls){
 const tabBar=document.querySelector('#list .meal-plan-tabs');
 const categoryRow=document.getElementById('categoryButtons');
 if(tabBar){const tabMenu=document.querySelector('#list .meal-plan-menu');if(tabMenu){tabBar.after(tabMenu);tabMenu.after(controls)}else tabBar.after(controls);if(categoryRow)controls.after(categoryRow)}
 else document.querySelector('#list')?.prepend(controls);
}
function renderGroceryViewToolbar(list){
 const bar=document.createElement('div');bar.className='top-controls';
 function add(label,svg,handler){const b=document.createElement('button');b.type='button';b.className='iconbtn top-action-icon';b.title=label;b.setAttribute('aria-label',label);b.innerHTML=svg;b.onclick=handler;bar.append(b)}
 const keyset=()=>new Set(getMasterGroceryItems().keys());
 const tickAll=checked=>{snapshot();for(const [key,item] of getMasterGroceryItems())setGroceryItemChecked(key,item,checked);localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));renderList()};
 add('Select all groceries','<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="m7 12 3 3 7-7"/></svg>',()=>tickAll(true));
 add('Deselect all groceries','<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7 12h10"/></svg>',()=>tickAll(false));
 const hide=localStorage.getItem('mealRotationHideCheckedGroceriesV1')==='true';
 add(hide?'Show checked groceries':'Hide checked groceries',hide?'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/><path d="M3 3l18 18"/></svg>':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>',()=>{localStorage.setItem('mealRotationHideCheckedGroceriesV1',String(!hide));renderList()});
 appendMealPlanSettingsGear(bar);
 list.append(bar);placeViewToolbar(bar);
 appendMealPlanSettingsPanel(list);
}
function moveMasterCategoryMeal(m,direction,singleStep){
 const group=meals.filter(x=>x.cat===m.cat&&x.rotation);
 const pos=group.findIndex(x=>x.id===m.id);if(pos<0)return;
 if(singleStep){
  const idx=pos+direction;if(idx<0||idx>=group.length)return;
  snapshot();const other=group[idx];const a=meals.indexOf(m),b=meals.indexOf(other);
  if(a<0||b<0)return;[meals[a],meals[b]]=[meals[b],meals[a]];
  clearOverridesForCat(m.cat);persist();renderList();return;
 }
  snapshot();
  function shift(target){const from=meals.indexOf(target);if(from<0)return;meals.splice(from,1);
   if(direction<0){const first=meals.findIndex(x=>x.cat===target.cat&&x.rotation);if(first<0)meals.push(target);else meals.splice(first,0,target)}
   else{let last=-1;meals.forEach((x,i)=>{if(x.cat===target.cat&&x.rotation)last=i});meals.splice(last+1,0,target)}
   clearOverridesForCat(target.cat);
  }
  shift(m);persist();renderList();
}
function bindMasterCategoryMove(button,m,direction){
 let timer=null,held=false;
 button.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse'&&e.button!==0)return;held=false;clearTimeout(timer);timer=setTimeout(()=>{held=true},500)});
 button.addEventListener('pointerup',e=>{clearTimeout(timer);if(held){e.preventDefault();e.stopPropagation();moveMasterCategoryMeal(m,direction,true)}});
 ['pointercancel','pointerleave'].forEach(ev=>button.addEventListener(ev,()=>clearTimeout(timer)));
 button.addEventListener('click',e=>{if(held){e.preventDefault();e.stopImmediatePropagation();held=false;return}moveMasterCategoryMeal(m,direction,false)},true);
 button.oncontextmenu=e=>{e.preventDefault();moveMasterCategoryMeal(m,direction,true)};
}
function openMasterCategoryEditMenu(category){
 if(!cats.includes(category))return;
 const overlay=document.createElement('div');overlay.className='master-cat-edit-overlay';overlay.style.cssText='position:fixed;inset:0;z-index:10005;background:#0008;display:flex;align-items:center;justify-content:center;padding:16px';
 const dialog=document.createElement('div');dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-label','Edit meal group');dialog.style.cssText='width:100%;max-width:420px;background:#fff;border-radius:16px;padding:22px;color:#242424;box-shadow:0 12px 36px #0003';
 const title=document.createElement('h3');title.textContent='Edit '+category;title.style.cssText='margin:0 0 15px';dialog.append(title);
 const row=document.createElement('div');row.className='meal-unified-actions';row.style.cssText='border-top:1px solid #ddd;padding-top:10px';
 function iconAction(kind,text,act){const b=document.createElement('button');b.type='button';b.className='iconbtn';setIconButton(b,kind,text);b.style.cssText='width:52px;height:48px';b.onclick=act;row.append(b)}
 function shift(dir){const ordered=currentMasterGroupOrder(),pos=ordered.indexOf(category),next=pos+dir;if(pos<0||next<0||next>=ordered.length)return;[ordered[pos],ordered[next]]=[ordered[next],ordered[pos]];if(writeMasterGroupOrder(ordered)){renderList();refreshMoveButtons()}}
 const moveLeft=document.createElement('button'),moveRight=document.createElement('button');
 for(const [button,kind,label,dir] of [[moveLeft,'left','Move group earlier',-1],[moveRight,'right','Move group later',1]]){button.type='button';button.className='iconbtn';setIconButton(button,kind,label);button.style.cssText='width:52px;height:48px';button.onclick=()=>shift(dir);row.append(button)}
 function refreshMoveButtons(){const ordered=currentMasterGroupOrder(),pos=ordered.indexOf(category);moveLeft.disabled=pos<=0;moveRight.disabled=pos<0||pos>=ordered.length-1;for(const button of [moveLeft,moveRight]){button.style.opacity=button.disabled?'0.3':'1';button.style.cursor=button.disabled?'not-allowed':'pointer'}}
 const hint=document.createElement('p');hint.className='category-order-hint';hint.style.cssText='font-size:13px;color:#666;margin:0 0 12px';hint.textContent='Long-press and drag a group, or use these arrows to change its display order.';dialog.append(hint);
 const addExisting=document.createElement('button');addExisting.type='button';addExisting.textContent='Add existing meals';addExisting.style.cssText='display:block;width:100%;padding:12px;margin:0 0 14px;border:1px solid #ccc;border-radius:9px;background:#f8f8f8;color:#222;font-size:16px;cursor:pointer';
 addExisting.onclick=async()=>{overlay.remove();await chooseExistingMealsForNewGroup(category,true);masterExpandedCategories.add(category);renderList()};
 dialog.append(addExisting);
 refreshMoveButtons();
 iconAction('rename','Rename group',()=>{overlay.remove();renameCategoryDirect(category)});
 iconAction('delete','Delete group',()=>{overlay.remove();openCategoryDeleteDialog(category)});
 iconAction('cancel','Cancel group editing',()=>overlay.remove());
 dialog.append(row);overlay.append(dialog);overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});document.body.append(overlay);
}
// Independent display choice for Meal Groups; never changes the active meal-plan tab.
function masterDisplayPlan(){return mealPlans.find(p=>p.id===activePlanId)}
function masterDisplayCategories(day){const plan=masterDisplayPlan();const raw=plan?.id===activePlanId?weekdayCategories[day]:plan?.weekdayCategories?.[day];return [...new Set((Array.isArray(raw)?raw:[raw]).filter(c=>typeof c==='string'&&cats.includes(c)))];}
function masterDisplayOrder(){const assigned=[];for(const day of orderedDays())for(const c of masterDisplayCategories(day))if(!assigned.includes(c))assigned.push(c);return [...assigned,...cats.filter(c=>!assigned.includes(c))];}
function masterDisplayColor(category){const colors=[...new Set(orderedDays().filter(d=>masterDisplayCategories(d).includes(category)).map(colorForDay))];if(!colors.length)return '#ffffff';if(colors.length===1)return colors[0];return 'linear-gradient(90deg, '+colors.flatMap((color,i)=>[`${color} ${100*i/colors.length}%`,`${color} ${100*(i+1)/colors.length}%`]).join(', ')+')';}

let masterReorderCategory=null;
function shiftMasterCategory(category,dir){
 const at=cats.indexOf(category),next=at+dir;
 if(at<0||next<0||next>=cats.length)return;
 snapshot();[cats[at],cats[next]]=[cats[next],cats[at]];
 persist();renderList();
}
 // Consistent meal-name gestures in My Rotation and Meal Groups.
let recipeBulkBackupAPI=null;
let recipeBulkMode=false,recipeBulkIds=new Set(),recipeBulkFocus=null,recipeBulkSuppress=null,recipeBulkBusy=false;
function bulkRecipeSelected(){return meals.filter(m=>recipeBulkIds.has(String(m.id)))}
function bulkRecipeRender(){const top=window.scrollY;renderList();window.scrollTo({top,behavior:'instant'});requestAnimationFrame(()=>window.scrollTo({top,behavior:'instant'}))}
function beginRecipeBulk(meal){if(showTop||editId!==null||recipeViewer||recipeBulkBusy)return;const top=scrollY;recipeBulkMode=true;recipeBulkIds.add(String(meal.id));recipeBulkFocus={cat:meal.cat,rotation:!!meal.rotation};recipeBulkSuppress=String(meal.id);masterGroupDragCleanup?.();masterGroupDragCleanup=null;updateRecipeBulkUI();window.scrollTo({top,behavior:'instant'});requestAnimationFrame(()=>window.scrollTo({top,behavior:'instant'}))}
function endRecipeBulk(){recipeBulkMode=false;recipeBulkIds.clear();recipeBulkFocus=null;recipeBulkSuppress=null;document.body.classList.remove('recipe-bulk-select');document.getElementById('recipeBulkToolbar')?.remove();document.querySelectorAll('.recipe-bulk-check').forEach(el=>el.remove());if(!showTop&&editId===null)bulkRecipeRender()}
function toggleRecipeBulk(meal,checked=null){const key=String(meal.id);if(checked??!recipeBulkIds.has(key))recipeBulkIds.add(key);else recipeBulkIds.delete(key);recipeBulkFocus={cat:meal.cat,rotation:!!meal.rotation};updateRecipeBulkUI()}
function bindRecipeBulkRow(row,meal){
 let hold=null,start=null;const stop=()=>{clearTimeout(hold);hold=null;start=null};
 row.addEventListener('pointerdown',e=>{if(recipeBulkMode){recipeBulkSuppress=null;e.stopImmediatePropagation();return}if(e.pointerType==='mouse'&&e.button!==0||e.target.closest('button,input,a,select'))return;start={x:e.clientX,y:e.clientY};hold=setTimeout(()=>{if(start)beginRecipeBulk(meal)},550)},{capture:true});
 row.addEventListener('pointermove',e=>{if(start&&Math.hypot(e.clientX-start.x,e.clientY-start.y)>10)stop()});for(const event of ['pointerup','pointercancel','pointerleave'])row.addEventListener(event,stop);
 row.addEventListener('click',e=>{if(!recipeBulkMode)return;if(recipeBulkSuppress!==null){recipeBulkSuppress=null;e.preventDefault();e.stopImmediatePropagation();return}if(e.target.closest('.recipe-bulk-check'))return;e.preventDefault();e.stopImmediatePropagation();toggleRecipeBulk(meal)},{capture:true});
}
function updateRecipeBulkUI(){
 if(!recipeBulkMode)return;for(const id of recipeBulkIds)if(!meals.some(m=>String(m.id)===id))recipeBulkIds.delete(id);document.body.classList.add('recipe-bulk-select');for(const button of document.querySelectorAll('.master-category-header .iconbtn,.master-add-group,[aria-label="Manage recipe labels"]'))button.disabled=true;
 for(const row of document.querySelectorAll('.master-category-meal[data-meal-id]')){const meal=meals.find(m=>String(m.id)===row.dataset.mealId);if(!meal)continue;let label=row.querySelector('.recipe-bulk-check');if(!label){label=document.createElement('label');label.className='recipe-bulk-check';const check=document.createElement('input');check.type='checkbox';check.className='check';check.setAttribute('aria-label','Select '+(meal.name||'Untitled meal'));check.onchange=()=>toggleRecipeBulk(meal,check.checked);label.append(check);row.prepend(label)}label.firstElementChild.checked=recipeBulkIds.has(String(meal.id))}
 let bar=document.getElementById('recipeBulkToolbar');if(!bar){bar=document.createElement('section');bar.id='recipeBulkToolbar';bar.setAttribute('aria-label','Selected recipes');bar.dataset.recipeEditDraft='';const count=document.createElement('div');count.className='recipe-bulk-count';count.setAttribute('role','status');bar.append(count);const actions=document.createElement('div');actions.className='recipe-bulk-actions';for(const [kind,label,action]of [['move','Move selected recipes',()=>openRecipeBulkEditor(true)],['rename','Edit selected recipes',()=>openRecipeBulkEditor(false)],['delete','Delete selected recipes',deleteRecipeBulk],['save','Select all / Deselect all',openRecipeBulkScopes],['cancel','Exit selection mode',endRecipeBulk]]){const b=document.createElement('button');b.type='button';setIconButton(b,kind,label);if(kind==='save')b.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="m7 12 3 3 7-7"/></svg>';const text=document.createElement('span');text.textContent=({move:'Move',rename:'Edit',delete:'Delete',save:'Select',cancel:'Done'})[kind];b.append(text);b.classList.add('recipe-bulk-labeled-action');b.dataset.needsSelection=String(['move','rename','delete'].includes(kind));b.onclick=action;actions.append(b)}bar.append(actions);document.body.append(bar)}
 bar.querySelector('.recipe-bulk-count').textContent=bulkRecipeSelected().map(meal=>meal.name||'Untitled meal').join(', ')||'No recipes selected';for(const b of bar.querySelectorAll('button[data-needs-selection="true"]'))b.disabled=!recipeBulkIds.size||recipeBulkBusy;
}
function recipeBulkDialog(title,returnFocus=null){
 const overlay=document.createElement('div');overlay.className='recipe-timer-dialog recipe-bulk-dialog';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label',title);overlay.dataset.recipeEditDraft='';const panel=document.createElement('div'),heading=document.createElement('strong');heading.textContent=title;panel.append(heading);
 const focused=document.activeElement,inert=[...document.body.children].map(el=>[el,el.inert]);for(const [el]of inert)el.inert=true;let closed=false;
 const layered=editId!==null&&mealEditorReturnView?.view==='groups'&&!recipeViewer&&!recipeEditorReturn,layer={id:'editor-dialog-'+(crypto.randomUUID?.()||Date.now()),close:null,overlay};
 if(layered){editorDialogStack.push(layer);window.history.pushState({...window.history.state,mealRotationEditorDialog:layer.id},'')}
 const close=(fromHistory=false)=>{if(closed||recipeBulkBusy)return;closed=true;if(layered){const index=editorDialogStack.indexOf(layer);if(index>=0)editorDialogStack.splice(index,1);if(fromHistory!==true&&window.history.state?.mealRotationEditorDialog===layer.id){stepEditorHistoryBack()}}overlay.remove();for(const [el,was]of inert)if(el.isConnected)el.inert=was;const target=focused?.isConnected?focused:typeof returnFocus==='function'?returnFocus():null;if(target?.isConnected&&!target.closest('[inert]'))target.focus({preventScroll:true})};
 overlay.onclick=e=>{if(e.target===overlay)close()};overlay.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();close()}if(e.key==='Tab'){const inputs=[...panel.querySelectorAll('button:not([disabled]),input,textarea,select,summary')].filter(el=>el.getClientRects().length),first=inputs[0],last=inputs.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}};overlay.append(panel);document.body.append(overlay);layer.close=close;return {overlay,panel,close};
}
function openRecipeBulkScopes(){
 const d=recipeBulkDialog('Select recipes'),visible=[...document.querySelectorAll('.master-category-meal')].filter(row=>row.getClientRects().length).map(row=>row.dataset.mealId),focus=recipeBulkFocus;
 const options=[];if(focus){if(focus.cat)options.push(['Select '+focus.cat+' · '+(focus.rotation?'In Rotation':'Ideas'),meals.filter(m=>m.cat===focus.cat&&!!m.rotation===focus.rotation).map(m=>String(m.id))]);options.push(['Select all in '+(focus.cat||'Unassigned'),meals.filter(m=>m.cat===focus.cat).map(m=>String(m.id))])}options.push(['Select expanded sections',visible],['Select all recipes across all groups',meals.map(m=>String(m.id))]);
 for(const [name,ids]of options){const b=document.createElement('button');b.type='button';b.className='smallbtn';b.textContent=name+' ('+ids.length+')';b.onclick=()=>{ids.forEach(id=>recipeBulkIds.add(id));updateRecipeBulkUI();d.close()};d.panel.append(b)}const none=document.createElement('button');none.type='button';none.className='smallbtn';none.textContent='Deselect all';none.onclick=()=>{recipeBulkIds.clear();updateRecipeBulkUI();d.close()};const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close selection options');close.onclick=d.close;d.panel.append(none,close);close.focus({preventScroll:true});
}
function validateRecipeBulkChange(ids,patch,allowEmpty=false,groups=cats){
 for(const key of ['rotation','favorite','adjusting','delete'])if(Object.hasOwn(patch,key)&&typeof patch[key]!=='boolean')throw Error('Invalid '+key+' change.');for(const key of ['addLabels','removeLabels'])if(patch[key]!==undefined&&(!Array.isArray(patch[key])||patch[key].some(label=>typeof label!=='string'||!label.trim())))throw Error('Invalid recipe labels.');
 if((!ids.length&&!allowEmpty)||ids.some(id=>!meals.some(m=>String(m.id)===id)))throw Error('The recipe selection changed. Select the recipes again.');if(patch.category&&!groups.includes(patch.category))throw Error('Choose an existing meal group.');
 if(patch.category===''&&patch.rotation===true)throw Error('Choose a meal group before adding unassigned recipes to rotation.');
 if(patch.rotation===true&&!patch.category&&meals.some(meal=>meal.cat===''&&ids.includes(String(meal.id))))throw Error('Choose a meal group before adding unassigned recipes to rotation.');
 if((patch.addLabels||[]).some(label=>(patch.removeLabels||[]).some(other=>labelKey(label)===labelKey(other))))throw Error('A label cannot be added and removed in the same update.');
 if(Object.hasOwn(patch,'category')){const groups=new Map();for(const m of meals){if(!m.linkGroup)continue;const cat=ids.includes(String(m.id))?patch.category:m.cat,key=JSON.stringify([m.linkGroup,cat]);if(groups.has(key)){const other=groups.get(key);if(ids.includes(String(m.id))&&m.cat!==patch.category||ids.includes(String(other.id))&&other.cat!==patch.category)throw Error('Shared copies of the same recipe cannot occupy the same group. Choose a different destination; no recipes were moved.')}groups.set(key,m)}}
}
function freezeRecipeBulkSchedule(schedules){
 preserveOtherMealPlanChoices(null,null,schedules);for(const plan of mealPlans)for(const entry of schedules.get(plan.id)||[]){if(!rotationSelectable(entry,plan))continue;const key=weekdaySlotKey(entry.day,entry.cat),meal=meals.find(m=>String(m.id)===String(entry.meal.id));if(!meal)continue;const choice=plan.cycleSlotChoices[key];if(!choice)continue;choice.retain=true;if(!entry.dependentSide&&(meal.cat!==entry.cat||!recipeMatchesFilters(meal,plan.weekdayRecipeFilters?.[key]||[])))choice.substitution=true}
 weekdayMealOverrides={...mealPlans.find(p=>p.id===activePlanId).weekdayMealOverrides};
}
// Shared with individual demotion: replace only removed occurrences, never cook them.
function detachRecipeOccurrences(ids,schedules,grocery,deferReplacements=false){
 const outgoing=[];for(const plan of mealPlans){const entries=schedules.get(plan.id)||[],selected=entries.filter(item=>ids.has(String(item.meal.id))),affected=cycleAffectedEntries(entries,selected,plan);outgoing.push(...affected.map(item=>({...item,planId:plan.id})));const slots=[];
  for(const item of selected){const key=weekdaySlotKey(item.day,item.cat),old=plan.cycleSlotChoices[key]||{},excluded=[...new Set([...(old.excludedMealIds||[]),...ids])];if(String(plan.occasionalMeals?.[item.day])===String(item.meal.id))delete plan.occasionalMeals[item.day];
   if(rotationGroupScheduled(plan,item.day,item.cat)){delete plan.weekdayMealOverrides[key];delete plan.cycleRetainedSlots[key];const raw=plan.weekdayCategories[item.day],groups=Array.isArray(raw)?raw:[raw];if(groups[0]===item.cat)delete plan.weekdayMealOverrides[item.day];const possible=automaticSlotCandidates(plan,item.day,item.cat,meals,entries).some(m=>!ids.has(String(m.id)));plan.cycleSlotChoices[key]={parentId:'',blockedParents:[],excludedMealIds:excluded,...(!possible?{empty:true}:{})};if(possible)slots.push({...item,planId:plan.id})}
   else plan.cycleSlotChoices[key]={...old,excludedMealIds:excluded};
  }
  if(slots.length)resolveRotatedMealSlots(plan,slots,entries.filter(item=>!affected.includes(item)));if(deferReplacements){for(const parent of entries)for(const id of parent.meal.linkedMealIds||[]){const target=meals.find(m=>String(m.id)===String(id));if(!target||!ids.has(String(id)))continue;const key=weekdaySlotKey(parent.day,target.cat),choice=plan.cycleSlotChoices[key]||{};plan.cycleSlotChoices[key]={...choice,excludedMealIds:[...new Set([...(choice.excludedMealIds||[]),String(id)])]}}}if(deferReplacements)for(const item of slots){const choice=plan.cycleSlotChoices[weekdaySlotKey(item.day,item.cat)];if(choice)choice.skipReplacement=true}
 }
 weekdayMealOverrides={...mealPlans.find(p=>p.id===activePlanId).weekdayMealOverrides};saveWeekdayMealOverrides();clearCycledCookingContexts(outgoing);reconcileRotatedGroceryChecks(grocery,outgoing);return outgoing;
}
function pruneBulkRecipeReferences(records,plans,ids){
 for(const meal of records){if(Array.isArray(meal.linkedMealIds))meal.linkedMealIds=meal.linkedMealIds.filter(id=>!ids.has(String(id)));if(meal.linkGroup&&records.filter(m=>m.linkGroup===meal.linkGroup).length<2)meal.linkGroup=''}
 for(const plan of plans){for(const item of Object.values(plan.weekSchedule?.slots||{}))for(const key of Object.keys(item.groceryChecks||{})){const occurrence=JSON.parse(JSON.parse(key)[0]);if(ids.has(occurrence[2])||occurrence[3].startsWith('linked:')&&ids.has(occurrence[3].slice(7)))delete item.groceryChecks[key]}for(const key of Object.keys(plan.occasionalMeals||{}))if(ids.has(String(plan.occasionalMeals[key])))delete plan.occasionalMeals[key];for(const map of [plan.weekdayMealOverrides,plan.cycleRetainedSlots])for(const key of Object.keys(map||{}))if(ids.has(String(map[key])))delete map[key];for(const [key,choice]of Object.entries(plan.cycleSlotChoices||{})){if(ids.has(String(choice.mealId)))delete plan.cycleSlotChoices[key];else{if(ids.has(String(choice.parentId)))choice.parentId='';if(Array.isArray(choice.blockedParents))choice.blockedParents=choice.blockedParents.filter(id=>!ids.has(String(id)));if(Array.isArray(choice.excludedMealIds))choice.excludedMealIds=choice.excludedMealIds.filter(id=>!ids.has(String(id)));if(ids.has(String(choice.avoidMealId)))delete choice.avoidMealId}}for(const [pool,state]of Object.entries(plan.favoriteRotationScores||{}))if(Object.keys(state.scores||{}).some(id=>ids.has(id)))delete plan.favoriteRotationScores[pool];
  for(const field of ['occurrences','assignedOn','assignedAt'])for(const key of Object.keys(plan.rotationCalendar?.[field]||{})){const parts=JSON.parse(key);if(ids.has(String(parts[2]))||ids.has(String(parts[3])))delete plan.rotationCalendar[field][key]}
  for(const key of Object.keys(plan.makeAheadChecks||{})){const occurrence=JSON.parse(JSON.parse(key)[0]);if(ids.has(String(occurrence[2]))||ids.has(String(occurrence[3])))delete plan.makeAheadChecks[key]}
 }
}
function pruneBulkRotationHistory(raw,ids){if(!raw)return raw;const prior=JSON.parse(raw);if(!prior||!Array.isArray(prior.meals)||!Array.isArray(prior.mealPlans))throw Error('Saved rotation history could not be checked. Export a backup before deleting recipes.');prior.meals=prior.meals.filter(m=>!ids.has(String(m.id)));pruneBulkRecipeReferences(prior.meals,prior.mealPlans,ids);for(const key of ['rotationOccurrences','cookingCycledContexts','cookedDateUpdates','favoriteRotationTurns'])if(Array.isArray(prior[key]))prior[key]=prior[key].filter(item=>!ids.has(String(item.mealId))&&!ids.has(String(item.parentId)));if(prior.lastRotationBefore)prior.lastRotationBefore=pruneBulkRotationHistory(prior.lastRotationBefore,ids);return JSON.stringify(prior)}
function restoreBulkRecipeSelections(saved){const current=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const [id,value]of Object.entries(saved))current[id]=value;localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(current))}
function preserveBulkEmptySlots(schedules){
 for(const plan of mealPlans){const before=schedules.get(plan.id)||[],current=queueWeekEntries(plan);for(const entry of current)if(rotationGroupScheduled(plan,entry.day,entry.cat)&&!before.some(old=>old.day===entry.day&&old.cat===entry.cat)){const key=weekdaySlotKey(entry.day,entry.cat);plan.cycleSlotChoices[key]={...plan.cycleSlotChoices[key],empty:true}}}
}
function reparentDeletedBulkChildren(ids,schedules,raw){
 let changed=false;for(const plan of mealPlans){const current=queueWeekEntries(plan);for(const old of schedules.get(plan.id)||[]){if(!rotationGroupScheduled(plan,old.day,old.cat)||!ids.has(String(old.linkedTo))||ids.has(String(old.meal.id)))continue;const found=current.find(e=>e.day===old.day&&e.cat===old.cat&&String(e.meal.id)===String(old.meal.id));if(!found)continue;
  const key=weekdaySlotKey(old.day,old.cat),choice=plan.cycleSlotChoices[key];if(choice)choice.parentId='';const previous=rotationOccurrenceKey({...old,planId:plan.id}),context=cookingContext(plan.id,old.day,old.cat,found.meal),next=cookingOccurrenceKey(context);
  for(const [target,prior]of [[cookingSessions.occurrences,raw.sessions.occurrences],[occurrenceScales.occurrences,raw.scales.occurrences]]){
   for(const [oldKey,record]of Object.entries(prior)){if(cookingOccurrenceKey(record.context)!==previous||record.context.cat!==old.cat)continue;const scoped=target===occurrenceScales.occurrences,updated={...context,...(scoped?{scaleGroupId:groupIdentity(context.cat,true)||context.cat}:{})},newKey=scoped?scaleOccurrenceKey(updated):next;
    if(target[newKey]&&newKey!==oldKey)throw Error('A linked side has separate saved progress that cannot be safely merged. No recipes were deleted.');target[newKey]={...JSON.parse(JSON.stringify(record)),context:updated};if(newKey!==oldKey)delete target[oldKey];
   }
  }
  for(const field of ['occurrences','assignedOn','assignedAt'])if(plan.rotationCalendar?.[field]&&Object.hasOwn(plan.rotationCalendar[field],previous)){plan.rotationCalendar[field][next]=plan.rotationCalendar[field][previous];delete plan.rotationCalendar[field][previous]}
  const timer=JSON.parse(localStorage.getItem(COOKING_TIMER_KEY)||'null');if(timer?.context&&cookingOccurrenceKey(timer.context)===previous){timer.context={...context};localStorage.setItem(COOKING_TIMER_KEY,JSON.stringify(timer))}
  for(const check of Object.keys(plan.makeAheadChecks||{})){const parts=JSON.parse(check);if(parts[0]!==previous)continue;parts[0]=next;plan.makeAheadChecks[JSON.stringify(parts)]=plan.makeAheadChecks[check];delete plan.makeAheadChecks[check]}changed=true;
 }}if(changed){writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales)}
}
function validateBulkScheduleResult(schedules,departing,allowedDays=[],creating=false){
 const affected=new Set(allowedDays.map(item=>JSON.stringify([item.planId,item.day])));for(const [planId,entries]of schedules)for(const entry of entries)if(departing.has(String(entry.meal.id)))affected.add(JSON.stringify([planId,entry.day]));
 for(const plan of mealPlans){const before=schedules.get(plan.id)||[],current=queueWeekEntries(plan);if(current.some(e=>departing.has(String(e.meal.id))))throw Error('A linked relationship would keep a selected recipe scheduled. Adjust its destination or linked meal before retrying.');
  const stable=entry=>JSON.stringify([entry.day,String(entry.meal.id),String(entry.linkedTo||'')]);const hiddenNewEligibility=entry=>creating&&entry.linkedTo==null&&!before.some(old=>old.day===entry.day&&old.cat===entry.cat)&&(weekSchedule(plan).slots[temporarySlotKey(entry.day,entry.cat)]?.kind==='empty'||weekSchedule(plan).slots[temporarySlotKey(entry.day,null)]?.kind==='empty');const old=before.filter(e=>!affected.has(JSON.stringify([plan.id,e.day]))).map(stable).sort(),next=current.filter(e=>!affected.has(JSON.stringify([plan.id,e.day]))&&!hiddenNewEligibility(e)).map(stable).sort();if(JSON.stringify(old)!==JSON.stringify(next))throw Error('This change would alter another scheduled or linked meal. Choose a different destination or change that meal explicitly first.');
 }
}

function applyEditorRecipeMutation(edit,transaction){
 const source=meals.find(m=>String(m.id)===edit.sourceId);if(!source)throw Error('This recipe no longer exists.');const members=sharedRecipeMembers(source),memberIds=new Set(members.map(m=>String(m.id))),destinations=new Set();
 // Commit new groups with the recipe, so cancel and failed saves leave no empty groups.
 for(const name of edit.newGroups||[])cats=[...cats,validateNewMealGroupName(name)];
 for(const draft of edit.memberships){if(draft.id!==null&&!memberIds.has(String(draft.id)))throw Error('A group membership changed. Close and reopen the editor.');if(draft.cat&&!cats.includes(draft.cat))throw Error('Choose an existing group.');if(draft.cat&&destinations.has(draft.cat))throw Error('This recipe already belongs to that group.');if(draft.cat)destinations.add(draft.cat)}
 const primary=edit.memberships.find(draft=>String(draft.id)===edit.sourceId),wasRotation=source.rotation;
 if(!primary)throw Error('The recipe group changed. Close and reopen the editor.');
 const keepUnassigned=!destinations.size;
 if(primary.cat&&!wasRotation&&edit.rotation)transaction.promotion=prepareRecipePromotion({...source,...edit.fields,cat:primary.cat},false);
 assignSharedRecipeFields(source,edit.fields);if(Object.hasOwn(edit.fields,'ingredientStepLinks')&&sharedRecipeMembers(source).some(record=>JSON.stringify(validRecipeIngredientLinks(record))!==JSON.stringify(record.ingredientStepLinks||[])))throw Error('Shared ingredient links do not match the saved recipe content.');
 if(Object.hasOwn(edit.fields,'linkedMealIds'))for(const [planId,entries]of transaction.schedules)for(const entry of entries)if(memberIds.has(String(entry.meal.id)))transaction.allowedDays.push({planId,day:entry.day});
 for(const draft of edit.memberships){if(draft.id===null||(!draft.cat&&!(keepUnassigned&&draft===primary)))continue;const record=meals.find(m=>String(m.id)===String(draft.id)),previousCategory=record.cat;record.cat=draft.cat;transaction.selected.add(String(record.id));if(draft===primary){const rotation=!!draft.cat&&edit.rotation;if((wasRotation&&!rotation)||(previousCategory&&!draft.cat))transaction.departing.add(String(record.id));record.rotation=rotation;if(!record.rotation)delete record.rotationPromotionPriority}}
 for(const member of members)if(!edit.memberships.some(draft=>String(draft.id)===String(member.id)&&(draft.cat||(keepUnassigned&&draft===primary))))transaction.removed.add(String(member.id));
 const additions=edit.memberships.filter(draft=>draft.id===null&&draft.cat);let group=source.linkGroup;if(additions.length&&!group)group='linked-'+source.id+'-'+Date.now();
 for(const member of members)if(!transaction.removed.has(String(member.id)))member.linkGroup=group||'';
 for(const draft of additions){const record={...JSON.parse(JSON.stringify(source)),id:id++,cat:draft.cat,rotation:edit.rotation,linkGroup:group};delete record.rotationPromotionPriority;meals.push(record);const selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');selections[String(record.id)]=grocerySelectionsForMeal(source,selections);localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selections))}
 for(const record of meals)if(record.linkGroup&&meals.filter(m=>m.linkGroup===record.linkGroup&&!transaction.removed.has(String(m.id))).length<2)record.linkGroup='';
 transaction.promotionMealId=primary?.cat?edit.sourceId:null;if(transaction.promotion?.day)transaction.allowedDays.push({planId:activePlanId,day:transaction.promotion.day});
}

function recipeBulkOperationId(ids,patch,options){
 // Only an identical requested mutation may resolve its failed bulk operation.
 const ordered=value=>Array.isArray(value)?value.map(ordered):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,ordered(value[key])])):value;
 return 'bulk:'+JSON.stringify(ordered({type:options.dependentRole?'dependent-role':'bulk-edit',targets:[...ids].map(String).sort(),patch,dependentRole:options.dependentRole||null,firstMealPlan:options.firstMealPlan||undefined}));
}
function applyRecipeBulk(ids,patch,options={}){
 const newGroup=options.firstMealPlan?.newGroup?validateNewMealGroupName(options.firstMealPlan.category):null;
 const groups=newGroup?[...cats,newGroup]:cats;
 validateRecipeBulkChange(ids,patch,!!options.dependentRole||!!options.createScheduledRecipe,groups);if(recipeBulkBusy)throw Error('A bulk update is already in progress.');if(groceryCheckStorageInvalid||cookingStorageInvalid||scaleStorageInvalid)throw Error('Saved recipe progress or groceries could not be read. Export a backup before making bulk changes.');
 const beforeStorage=recipeBulkBackupAPI.capture();recipeBulkBackupAPI.validate(beforeStorage);const before=JSON.parse(captureState()),memory={id,cats,meals,mealPlans,weekdayCategories,weekdayMealOverrides,cookingSessions,occurrenceScales,groceryOccurrenceChecks,recipeLabelCatalog,excluded:masterGroceryExcludedMealKeys,linked:new Set(previouslyActiveLinkedIds),recipeStates:new Map(cookingRecipeStates),signature:cookingScheduleSignature};
 const raw=JSON.parse(JSON.stringify({sessions:cookingSessions,scales:occurrenceScales}));const selected=new Set(ids),removed=new Set(patch.delete?ids:[]),transaction={selected,removed,allowedDays:[],promotion:null,promotionMealId:null};let result=false;recipeBulkBusy=true;
 try{
  bulkRecipeStorageDraft=new Map(Array.from({length:mealBulkStorageBase.length},(_,i)=>{const key=mealBulkStorageBase.key(i);return [key,mealBulkStorageBase.getItem(key)]}));if(newGroup||options.createScheduledRecipe)cats=[...groups];meals=JSON.parse(JSON.stringify(meals));mealPlans=JSON.parse(JSON.stringify(mealPlans));weekdayMealOverrides={...weekdayMealOverrides};cookingSessions=JSON.parse(JSON.stringify(cookingSessions));occurrenceScales=JSON.parse(JSON.stringify(occurrenceScales));groceryOccurrenceChecks=JSON.parse(JSON.stringify(groceryOccurrenceChecks));recipeLabelCatalog=[...recipeLabelCatalog];masterGroceryExcludedMealKeys=new Set(masterGroceryExcludedMealKeys);
  saveActiveMealPlan();const schedules=new Map(mealPlans.map(p=>[p.id,queueWeekEntries(p)])),grocery=captureGroceryCheckStates();preserveOtherMealPlanChoices(null,null,schedules);
  const departing=new Set();transaction.departing=departing;transaction.schedules=schedules;
  const sharedIds=new Set(selectedSharedRecipeIds(ids));for(const meal of meals){if(selected.has(String(meal.id))){if(Object.hasOwn(patch,'category')){meal.cat=patch.category;if(!patch.category){departing.add(String(meal.id));meal.rotation=false;delete meal.rotationPromotionPriority}}if(patch.rotation!==undefined){if(!patch.rotation&&meal.rotation)departing.add(String(meal.id));meal.rotation=patch.rotation;if(!meal.rotation)delete meal.rotationPromotionPriority}}if(!sharedIds.has(String(meal.id)))continue;if(patch.favorite!==undefined){if(patch.favorite)meal.favorite=true;else delete meal.favorite}if(patch.adjusting!==undefined){if(patch.adjusting)meal.needsTweaking=true;else{delete meal.needsTweaking;delete meal.needsTweakingNote}}if(patch.addLabels?.length||patch.removeLabels?.length){const remove=new Set((patch.removeLabels||[]).map(labelKey));meal.labels=(Array.isArray(meal.labels)?[...meal.labels]:[]).filter(label=>!remove.has(labelKey(label)));for(const label of patch.addLabels||[])if(!meal.labels.some(old=>labelKey(old)===labelKey(label)))meal.labels.push(label)}}
  if(options.viewerEdit)applyViewerRecipeMutation(options.viewerEdit,before);if(options.editor)applyEditorRecipeMutation(options.editor,transaction);if(options.dependentRole)applyDependentRoleMutation(options.dependentRole,transaction);if(options.createScheduledRecipe)addScheduledRecipeDraft(options.createScheduledRecipe,transaction);
  if(patch.addLabels?.length){before.bulkRecipeUndoLabels=[...recipeLabelCatalog];for(const label of patch.addLabels)if(!recipeLabelCatalog.some(old=>labelKey(old)===labelKey(label)))recipeLabelCatalog.push(label);saveRecipeLabelCatalog()}
  const moved=meals.filter(m=>selected.has(String(m.id))&&memory.meals.some(old=>String(old.id)===String(m.id)&&(old.cat!==m.cat||!!old.rotation!==!!m.rotation))),promoted=moved.filter(m=>m.rotation&&!memory.meals.find(old=>String(old.id)===String(m.id)).rotation);
  const priority=Math.max(Date.now(),...meals.map(m=>Number(m.rotationPromotionPriority)||0))+promoted.length;promoted.forEach((m,i)=>m.rotationPromotionPriority=priority-i);
  for(const category of new Set(moved.filter(m=>m.rotation).map(m=>m.cat))){const incoming=moved.filter(m=>m.cat===category&&m.rotation);meals=meals.filter(m=>!incoming.includes(m));const first=meals.findIndex(m=>m.cat===category&&m.rotation);meals.splice(first<0?meals.length:first,0,...incoming)}
  const ideas=moved.filter(m=>!m.rotation);meals=meals.filter(m=>!ideas.includes(m)).concat(ideas);
  if(removed.size){for(const id of removed)departing.add(id);meals=meals.filter(m=>!removed.has(String(m.id)))}
  freezeRecipeBulkSchedule(schedules);if(!departing.size)preserveBulkEmptySlots(schedules);if(departing.size)detachRecipeOccurrences(departing,schedules,grocery,true);else{saveWeekdayMealOverrides();reconcileRotatedGroceryChecks(grocery,[])}
  if(removed.size){if(cookingTimer&&removed.has(String(cookingTimer.recipeId))){const owner=memory.meals.find(m=>String(m.id)===String(cookingTimer.recipeId)),peer=owner?.linkGroup&&meals.find(m=>memory.meals.some(old=>String(old.id)===String(m.id)&&old.linkGroup===owner.linkGroup));if(peer)localStorage.setItem(COOKING_TIMER_KEY,JSON.stringify({...cookingTimer,recipeId:String(peer.id),recipeName:peer.name,context:null}));else localStorage.removeItem(COOKING_TIMER_KEY)}reparentDeletedBulkChildren(removed,schedules,raw);pruneBulkRecipeReferences(meals,mealPlans,removed);weekdayMealOverrides={...mealPlans.find(p=>p.id===activePlanId).weekdayMealOverrides};const selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');before.bulkRecipeUndoSelections={};for(const id of removed){if(Object.hasOwn(selections,id))before.bulkRecipeUndoSelections[id]=selections[id];delete selections[id]}localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selections));const history=pruneBulkRotationHistory(localStorage.getItem(ROTATION_BACK_KEY),removed);if(history)localStorage.setItem(ROTATION_BACK_KEY,history);for(const plan of mealPlans){const key='mealRotationLastTopMealIdsV1:'+plan.id,raw=localStorage.getItem(key);if(raw)localStorage.setItem(key,JSON.stringify(JSON.parse(raw).filter(id=>!removed.has(String(id)))))}before.bulkRecipeUndoExclusions=[...masterGroceryExcludedMealKeys].filter(key=>removed.has(String(key).slice(String(key).lastIndexOf('::')+2)));masterGroceryExcludedMealKeys=new Set([...masterGroceryExcludedMealKeys].filter(key=>!removed.has(String(key).slice(String(key).lastIndexOf('::')+2))));saveMasterGroceryMealExclusions();resetCookingContexts(c=>removed.has(String(c.mealId))||removed.has(String(c.parentId)));clearOccurrenceScales(c=>removed.has(String(c.mealId))||removed.has(String(c.parentId)))}
  for(const plan of mealPlans){const prior=memory.mealPlans.find(p=>p.id===plan.id);for(const [key,choice]of Object.entries(plan.cycleSlotChoices||{})){const old=prior?.cycleSlotChoices?.[key];if(old&&String(old.mealId)===String(choice.mealId)){if(Object.hasOwn(old,'retain'))choice.retain=old.retain;else delete choice.retain}}}
  if(options.createScheduledRecipe){const draft=options.createScheduledRecipe,created=meals.find(meal=>meal.id===transaction.createdRecipeId);withSchedulingPlan(draft.target.planId,()=>applyManualWeekdayMeal(draft.target.day,draft.target.category,created,null,!!draft.target.occasional,{quiet:true,schedulingOnly:true,beforeState:before}));transaction.allowedDays.push({planId:draft.target.planId,day:draft.target.day})}
  if(options.firstMealPlan){
   const {planId,day,category,previous}=options.firstMealPlan,meal=meals.find(record=>String(record.id)===ids[0]);
   if(previous&&(previous.planId!==planId||previous.day!==day)){
    withSchedulingPlan(previous.planId,plan=>{delete plan.occasionalMeals[previous.day]});
    transaction.allowedDays.push(previous);
   }
   withSchedulingPlan(planId,()=>applyManualWeekdayMeal(day,category,meal,null,false,{quiet:true,startGroup:true,automatic:true}));
   transaction.allowedDays.push({planId,day});
  }
  if(transaction.promotion&&transaction.promotionMealId){const promoted=meals.find(m=>String(m.id)===transaction.promotionMealId);if(promoted)finishRecipePromotion(promoted,transaction.promotion)}reconcileActiveLinkedMeals();validateBulkScheduleResult(schedules,departing,transaction.allowedDays,!!options.createScheduledRecipe);reconcileRotatedGroceryChecks(grocery,[]);persist();saveActiveMealPlan();const proposed=recipeBulkBackupAPI.capture();recipeBulkBackupAPI.validate(proposed);bulkRecipeStorageDraft=null;recipeBulkBackupAPI.restore(proposed,{id:options.viewerEdit?options.viewerEdit.owner:options.createScheduledRecipe?options.createScheduledRecipe.owner:options.editor?'recipe:'+options.editor.sourceId:recipeBulkOperationId(ids,patch,options),kind:options.viewerEdit?'viewer-recipe-edit':options.createScheduledRecipe?'recipe-create-schedule':options.editor?'recipe-edit':'bulk-edit',ownerId:options.viewerEdit?options.viewerEdit.owner:options.createScheduledRecipe?options.createScheduledRecipe.owner:options.editor?'recipe:'+options.editor.sourceId:null,retry:()=>applyRecipeBulk([...ids],JSON.parse(JSON.stringify(patch)),JSON.parse(JSON.stringify(options)))});
  const keys=[...new Set([...Object.keys(raw.sessions.occurrences).filter(k=>!cookingSessions.occurrences[k]),...Object.keys(raw.scales.occurrences).filter(k=>!occurrenceScales.occurrences[k])])];if(keys.length)before.skippedCookingState={keys,sessions:raw.sessions.occurrences,scales:raw.scales.occurrences};before.bulkRecipeUndoNewSelections=meals.filter(m=>!memory.meals.some(old=>String(old.id)===String(m.id))).map(m=>String(m.id));snapshot(JSON.stringify(before));if(options.createScheduledRecipe)finishScheduleChangeUndo(before);result=true;
 }catch(error){bulkRecipeStorageDraft=null;id=memory.id;cats=memory.cats;meals=memory.meals;mealPlans=memory.mealPlans;weekdayCategories=memory.weekdayCategories;weekdayMealOverrides=memory.weekdayMealOverrides;cookingSessions=memory.cookingSessions;occurrenceScales=memory.occurrenceScales;groceryOccurrenceChecks=memory.groceryOccurrenceChecks;recipeLabelCatalog=memory.recipeLabelCatalog;masterGroceryExcludedMealKeys=memory.excluded;previouslyActiveLinkedIds=memory.linked;cookingRecipeStates.clear();for(const [key,value]of memory.recipeStates)cookingRecipeStates.set(key,value);cookingScheduleSignature=memory.signature;throw error}
 finally{bulkRecipeStorageDraft=null;recipeBulkBusy=false}
 if(result){for(const removedId of removed)mealPersistence.cancelOwner('recipe:'+removedId);if(removed.size&&cookingTimer){const restored=readCookingTimer();if(restored?.id===cookingTimer.id){cookingTimer=restored;syncCookingTimer()}else if(removed.has(String(cookingTimer.recipeId)))cancelCookingTimer()}if(options.render!==false){if(recipeBulkMode)endRecipeBulk();else bulkRecipeRender()}}return result;
}
async function confirmDeleteRecipes(ids){
 const expanded=selectedSharedRecipeIds(ids),count=recipeIdentityCount(expanded);if(!expanded.length||!count)return null;
 if(await appDialog('Delete '+count+' recipe'+(count===1?'':'s')+' from all groups?',null,'tracking-remove',[],'Selected recipes: '+[...new Set(meals.filter(meal=>expanded.includes(String(meal.id))).map(meal=>meal.name||'Untitled meal'))].join(', ')+'. The recipes will be deleted from every group. Scheduled slots and references will be cleaned up. Linked recipes that are not selected will be kept.'+(cookingTimer&&expanded.includes(String(cookingTimer.recipeId))?' Their active timer will also stop.':''))!==true)return null;return expanded;
}
async function deleteRecipeBulk(){const ids=await confirmDeleteRecipes(bulkRecipeSelected().map(m=>String(m.id)));if(!ids)return;try{applyRecipeBulk(ids,{delete:true})}catch(error){await showAppMessage('Bulk delete could not be completed: '+error.message)}}

function newMealGroupButton(onCreated){
 const add=document.createElement('button');add.type='button';add.className='smallbtn';add.textContent='+ New Group';add.style.minHeight='44px';add.setAttribute('aria-haspopup','dialog');
 add.onclick=()=>{
  const prompt=recipeBulkDialog('New group');
  const field=document.createElement('input');field.type='text';field.setAttribute('aria-label','New group name');field.className='recipe-bulk-new-group';
  const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','alert');
  const buttons=document.createElement('div');buttons.className='meal-unified-actions';
  const create=document.createElement('button');create.type='button';setIconButton(create,'save','Create group');
  const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Cancel new group');close.onclick=prompt.close;
  create.onclick=()=>{
   let group;
   try{group=createMealGroup(field.value)}
   catch(problem){error.textContent=problem.message;field.focus({preventScroll:true});return}
   prompt.close();onCreated(group);
  };
  field.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();create.click()}};
  buttons.append(create,close);prompt.panel.append(field,error,buttons);field.focus({preventScroll:true});
 };
 return add;
}
function chooseBulkValue(title,value,options,onSelect,allowNewGroup=false,returnFocus=null){
 const d=recipeBulkDialog(title,returnFocus),list=document.createElement('div');list.className='recipe-bulk-choice-list';let draft=value;
 function draw(){list.replaceChildren();for(const [key,text]of options()){const label=document.createElement('label');label.className='recipe-bulk-choice';const check=document.createElement('input');check.type='radio';check.name='bulk-choice';check.className='check';check.checked=draft===key;check.value=key;check.onchange=()=>{draft=key};label.append(check,document.createTextNode(text));list.append(label)}}
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button');save.type='button';setIconButton(save,'save','Confirm '+title.toLowerCase());const cancel=document.createElement('button');cancel.type='button';setIconButton(cancel,'cancel','Cancel '+title.toLowerCase());save.onclick=()=>{onSelect(draft);d.close()};cancel.onclick=d.close;actions.append(save,cancel);d.panel.append(list);
 if(allowNewGroup)d.panel.append(newMealGroupButton(group=>{onSelect(group);d.close();bulkRecipeRender()}));
 d.panel.append(actions);draw();cancel.focus({preventScroll:true});
}
function bulkChoiceField(parent,label,options,onChange,allowNewGroup=false){
 const wrapper=document.createElement('div');wrapper.className='recipe-bulk-field';const title=document.createElement('span');title.textContent=label;const button=document.createElement('button');button.type='button';button.className='recipe-bulk-value';button.setAttribute('aria-label',label);button.setAttribute('aria-haspopup','dialog');let value='';const field={get value(){return value}};
 function set(next){value=next;button.textContent=options().find(([key])=>key===next)?.[1]||'Unchanged';onChange()}
 button.textContent='Unchanged';button.onclick=()=>chooseBulkValue(label,value,options,set,allowNewGroup);wrapper.append(title,button);parent.append(wrapper);return field;
}

function openRecipeBulkEditor(moveOnly=false){
 const ids=bulkRecipeSelected().map(m=>String(m.id));if(!ids.length)return;const d=recipeBulkDialog(moveOnly?'Move '+ids.length+' recipes':'Edit '+ids.length+' recipes'),body=document.createElement('div');body.className='recipe-bulk-fields';const names=document.createElement('p');names.className='recipe-bulk-selected-names';names.textContent=bulkRecipeSelected().map(meal=>meal.name||'Untitled meal').join(', ');body.append(names);const hint=document.createElement('p');hint.className='muted';hint.textContent='Unchanged leaves each recipe as it is.';if(!moveOnly)body.append(hint);
 const select=(label,options)=>{const wrapper=document.createElement('label');wrapper.className='recipe-bulk-field';const text=document.createElement('span');text.textContent=label;const input=document.createElement('select');input.setAttribute('aria-label',label);for(const [value,name]of [['','Unchanged'],...options]){const option=document.createElement('option');option.value=value;option.textContent=name;input.append(option)}wrapper.append(text,input);body.append(wrapper);return input};
 const category=select('Meal group',[['__unassigned__','Unassigned'],...cats.map(cat=>[cat,cat])]),rotation=select('Rotation status',[['true','In Rotation'],['false','Ideas']]);let favorite,adjusting;body.append(newMealGroupButton(name=>{const option=document.createElement('option');option.value=option.textContent=name;category.append(option);category.value=name;changed()}));
 if(!moveOnly){favorite=select('Family Favorites',[['true','Mark as favorite'],['false','Remove favorite status']]);adjusting=select('Needs Adjusting',[['true','Mark as Needs Adjusting (keep individual notes)'],['false','Remove status and its notes']])}
 const patch=()=>{const result={};if(category.value)result.category=category.value==='__unassigned__'?'':category.value;for(const [key,input]of [['rotation',rotation],['favorite',favorite],['adjusting',adjusting]])if(input?.value)result[key]=input.value==='true';return result};
 const impact=document.createElement('p');impact.className='muted recipe-bulk-impact';body.append(impact);const actions=document.createElement('div');actions.className='meal-unified-actions';const apply=document.createElement('button');apply.type='button';apply.className='smallbtn';apply.textContent='Apply changes';apply.setAttribute('aria-label','Apply to selected recipes');apply.disabled=true;const cancel=document.createElement('button');cancel.type='button';cancel.className='smallbtn';cancel.textContent='Cancel';cancel.setAttribute('aria-label','Cancel bulk edit');cancel.onclick=d.close;actions.append(apply,cancel);d.panel.append(body,actions);
 const changed=()=>{const proposed=patch();apply.disabled=!Object.keys(proposed).length;const scheduled=mealPlans.flatMap(plan=>getDisplayedWeekdayMealsForPlan(plan)).filter(e=>ids.includes(String(e.meal.id)));impact.textContent=proposed.rotation===false&&scheduled.length?'Scheduled selections will be replaced where an eligible recipe is available; otherwise their slots will be empty. Linked recipe definitions are kept.':''};body.oninput=changed;body.onchange=changed;
 apply.onclick=async()=>{if(recipeBulkBusy)return;apply.disabled=true;try{const proposed=patch();validateRecipeBulkChange(ids,proposed);if(proposed.adjusting===false&&meals.some(m=>selectedSharedRecipeIds(ids).includes(String(m.id))&&(m.needsTweaking||m.needsTweakingNote))){if(!await confirmNeedsTweakingRemoval('This removes the warning and its note from the selected recipes. Other recipe details stay unchanged.'))return}applyRecipeBulk(ids,proposed);d.close()}catch(error){await showAppMessage('Bulk update could not be completed: '+error.message)}finally{if(d.overlay.isConnected)changed()}};cancel.focus({preventScroll:true});
}

function bindGroupMealPress(name,meal){
 let timer=null,pressed=false,held=false,suppressClick=false,pressPoint=null;
 const stop=()=>{clearTimeout(timer);timer=null};
 name.style.userSelect='none';name.style.webkitUserSelect='none';name.style.webkitTouchCallout='none';name.style.touchAction='pan-y';
 name.addEventListener('selectstart',e=>e.preventDefault());
 name.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse'&&e.button!==0)return;stop();pressed=true;held=false;pressPoint={x:e.clientX,y:e.clientY};timer=setTimeout(()=>{if(pressed){held=true;suppressClick=true;if(!showTop)beginRecipeBulk(meal)}},550)});
 name.addEventListener('pointermove',e=>{if(pressed&&pressPoint&&Math.hypot(e.clientX-pressPoint.x,e.clientY-pressPoint.y)>10){stop();pressed=false}});
 name.addEventListener('pointerup',e=>{stop();const wasHeld=pressed&&held;pressed=false;if(wasHeld){e.preventDefault();if(!showTop){if(!recipeBulkMode)beginRecipeBulk(meal)}else{suppressClick=true;openSavedMealRecipe(meal)}}});
 ['pointerleave','pointercancel'].forEach(ev=>name.addEventListener(ev,()=>{stop();pressed=false}));
 name.addEventListener('click',e=>{if(suppressClick){e.preventDefault();e.stopImmediatePropagation();suppressClick=false;return}openTopMealActionMenu(null,meal.cat,meal)});
 name.oncontextmenu=e=>e.preventDefault();
}
function openSavedMealRecipe(meal,context=null,navigationOrigin=null){openRecipeViewer(meal,context,true,null,navigationOrigin)}

const ideasRecipeNameCollator=new Intl.Collator(undefined,{sensitivity:'base'});
function masterRecipeOrder(category,highlights=scheduledRecipeHighlights()){
 const entries=meals.filter(meal=>meal.cat===category),rotation=entries.filter(meal=>!!meal.rotation),ideas=entries.filter(meal=>!meal.rotation).sort((a,b)=>ideasRecipeNameCollator.compare(String(a.name||''),String(b.name||'')));
 if(manualRecipeOrdering)return [...rotation,...ideas];
 const days=orderedDays(),ranks=new Map();
 for(const entry of highlights.scheduledEntries){
  const plan=mealPlans.find(plan=>plan.id===entry.planId),current=plan?.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides}:plan;
  const manual=(entry.occasional&&!entry.linkedTo)||manualWeekdayMealChoice(current,entry.day,entry.cat,entry.meal.id);
  const rank=[manual?0:1,days.indexOf(entry.day)],key=String(entry.meal.id),prior=ranks.get(key);
  if(prior){prior[0]=Math.min(prior[0],rank[0]);prior[1]=Math.min(prior[1],rank[1])}else ranks.set(key,rank);
 }
 const rank=meal=>{const scheduled=ranks.get(String(meal.id));if(scheduled)return scheduled;if(Number.isFinite(meal.rotationPromotionPriority))return [2,-meal.rotationPromotionPriority];const time=meal.lastCooked?new Date(meal.lastCooked).getTime():NaN;return Number.isFinite(time)?[4,time]:[3,0]};
 const names=(a,b)=>String(a.name||'').localeCompare(String(b.name||''),undefined,{sensitivity:'base',numeric:true});
 return [...rotation.sort((a,b)=>{const x=rank(a),y=rank(b);return x[0]-y[0]||x[1]-y[1]||(x[0]>=3?names(a,b):0)}),...ideas];
}
function scheduledRecipeHighlights(preview=null,{activePlanBadgesOnly=false}={}){
 const featuredColorById=new Map();
 const scheduledDaysByMeal=new Map();
 // Weekday-only labels; recipes are allocated distinctly across tabs where possible.
 const multiplePlansVisible=showMealPlanTabs&&mealPlans.length>1;
 const scheduledEntries=[];
 if(!multiplePlansVisible){
  // Match My Rotation exactly when tabs are hidden: only the active plan
  // contributes highlighted recipes, weekday badges, and active groups.
  const activePlan=mealPlans.find(p=>p.id===activePlanId);
  for(const entry of getDisplayedWeekdayMeals()){
   scheduledEntries.push({...entry,planName:activePlan?.name||'',planId:activePlanId});
  }
 }else{
  // When tabs are visible, preserve the cross-tab allocation and highlights.
  const usedForLabels=new Map();
  for(const plan of mealPlans){
   const current=plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan;
   for(const entry of getDisplayedWeekdayMealsForPlan(current,usedForLabels)){
    scheduledEntries.push({...entry,planName:plan.name,planId:plan.id});
    if(!usedForLabels.has(entry.cat))usedForLabels.set(entry.cat,new Set());
    usedForLabels.get(entry.cat).add(String(entry.meal.id));
   }
  }
 }
 // The chooser previews one pending slot without changing the saved schedule.
 // Reuse the same weekday colors and multi-day badges as Meal Groups.
 if(preview?.meal){
  const index=scheduledEntries.findIndex(entry=>entry.planId===activePlanId&&entry.day===preview.day&&(preview.occasional?entry.occasional&&!entry.linkedTo:entry.cat===preview.category));
  const entry={day:preview.day,cat:preview.category||preview.meal.cat,meal:preview.meal,planId:activePlanId,planName:mealPlans.find(plan=>plan.id===activePlanId)?.name||''};
  if(index>=0)scheduledEntries.splice(index,1,entry);
  else{
   scheduledEntries.push(entry);const days=orderedDays();
   scheduledEntries.sort((a,b)=>mealPlans.findIndex(plan=>plan.id===a.planId)-mealPlans.findIndex(plan=>plan.id===b.planId)||days.indexOf(a.day)-days.indexOf(b.day));
  }
 }
 // Meal Groups shows the same scheduled days for every membership of a shared recipe.
 const sharedMemberIds=new Map();
 if(activePlanBadgesOnly)for(const meal of meals){
  if(!meal.linkGroup)continue;
  if(!sharedMemberIds.has(meal.linkGroup))sharedMemberIds.set(meal.linkGroup,[]);
  sharedMemberIds.get(meal.linkGroup).push(String(meal.id));
 }
 for(const entry of scheduledEntries){
  if(activePlanBadgesOnly&&entry.planId!==activePlanId)continue;
  const ids=sharedMemberIds.get(entry.meal.linkGroup)||[String(entry.meal.id)];
  for(const key of ids){
   if(!featuredColorById.has(key))featuredColorById.set(key,colorForDay(entry.day));
   if(!scheduledDaysByMeal.has(key))scheduledDaysByMeal.set(key,new Map());
   const dayPlans=scheduledDaysByMeal.get(key);
   if(!dayPlans.has(entry.day))dayPlans.set(entry.day,[]);
   dayPlans.get(entry.day).push(entry);
  }
 }
 return {featuredColorById,scheduledDaysByMeal,scheduledEntries};
}
function appendScheduledRecipeWeekdays(row,meal,scheduledDaysByMeal){
 const scheduledDays=scheduledDaysByMeal.get(String(meal.id));
 if(!scheduledDays?.size)return;
 const dayTag=document.createElement('span');dayTag.className='master-meal-weekdays';
 dayTag.textContent=orderedDays().filter(day=>scheduledDays.has(day)).map(day=>day.slice(0,3).toUpperCase()).join(' · ');
 if(row.classList.contains('master-category-meal')&&scheduledDays.size>1){
  const days=dayTag.textContent.split(' · ');dayTag.replaceChildren();days.forEach((day,index)=>{if(index){const separator=document.createElement('span');separator.className='master-weekday-separator';separator.textContent=' · ';separator.setAttribute('aria-hidden','true');dayTag.append(separator)}const token=document.createElement('span');token.className='master-weekday-token';token.textContent=day;dayTag.append(token)});
 }
 dayTag.title='Scheduled: '+[...scheduledDays.entries()].map(([day,entries])=>day+' ('+[...new Set(entries.map(entry=>entry.planName))].join(', ')+')').join('; ');
 row.append(dayTag);
}
// Onboarding reuses the existing creation/import and weekday-assignment workflows.
function needsRotationSetup(){
 if(!meals.some(meal=>cats.includes(meal.cat)))return false;
 return !mealPlans.some(plan=>weekdays.some(day=>Object.hasOwn(plan.id===activePlanId?weekdayCategories:plan.weekdayCategories||{},day)));
}
function appendRotationSetupPrompt(parent){
 if(!needsRotationSetup())return;
 const section=document.createElement('section');section.className='rotation-setup-prompt';section.style.cssText='padding:12px;margin:10px 0;border:1px solid #d5dde6;border-top:2px solid #bcc8d3;border-radius:10px;background:#f8fafc';
 const text=document.createElement('p');text.textContent='Pick a day to plan your first meal. You can set up the rest of the week later.';text.style.margin='0 0 8px';
 const first=meals[0],recipe=first&&meals.every(meal=>sharedRecipeIdentity(meal)===sharedRecipeIdentity(first))?first:null;
 const button=document.createElement('button');button.type='button';button.className='smallbtn';button.style.minHeight='44px';button.textContent='Set Up Your Rotation';button.onclick=()=>openRotationSetup(recipe);section.append(text,button);parent.append(section);
}
function chooseGroupForFirstMeal(meal,previous=null){
 const d=recipeBulkDialog('Choose a meal group for '+meal.name),list=document.createElement('div');
 list.className='meal-group-picker-options';list.setAttribute('role','group');list.setAttribute('aria-label','Meal groups');
 const pick=category=>{d.close();openRotationSetup(meal,{category,previous})};
 for(const category of cats){
  const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';
  label.append(check,document.createTextNode(category));list.append(label);
  check.onchange=()=>{if(check.checked)pick(category)};
 }
 const row=document.createElement('div');row.className='first-meal-new-group';
 const check=document.createElement('input');check.type='checkbox';check.setAttribute('aria-label','Create and choose new group');
 const field=document.createElement('input');field.type='text';field.className='recipe-bulk-new-group';field.placeholder='New group';field.setAttribute('aria-label',field.placeholder);
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','alert');error.hidden=true;
 check.onchange=()=>{
  if(!check.checked)return;
  let category;
  try{category=validateNewMealGroupName(field.value)}
  catch(problem){check.checked=false;error.textContent=problem.message;error.hidden=false;field.setAttribute('aria-invalid','true');field.focus({preventScroll:true});return}
  d.close();openRotationSetup(meal,{category,previous,newGroup:true});
 };
 field.oninput=()=>{error.hidden=true;field.removeAttribute('aria-invalid')};
 row.append(check,field);
 const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close setup');close.style.minHeight='44px';close.onclick=d.close;
 const choices=document.createElement('div');choices.className='first-meal-group-choices';
 if(cats.length)choices.append(list);
 choices.append(row);
 d.panel.append(choices,error,close);close.focus({preventScroll:true});
}
function showFirstRotationTip(day,category){
 const button=document.querySelector('.rotation-heading-actions button[aria-label="Rotate Meals"]'),header=button?.closest('.rotation-compact-header');
 if(!header)return;
 const tip=document.createElement('aside');tip.className='first-rotation-tip';
 tip.innerHTML='<svg class="first-rotation-arrow" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 16V3m-5 5 5-5 5 5"/></svg>';
 const message=document.createElement('p');message.setAttribute('role','status');
 const group=document.createElement('strong');group.textContent=category;
 message.append('The ',group,' group is scheduled for '+day+'. Tap Rotate Meals to pick the next recipe from this group.');
 const close=document.createElement('button');close.type='button';close.className='iconbtn first-rotation-close';setIconButton(close,'cancel','Dismiss rotation tip');close.onclick=()=>{tip.remove();button.focus({preventScroll:true})};
 tip.append(message,close);header.after(tip);
 const anchor=button.getBoundingClientRect(),bounds=tip.getBoundingClientRect();
 tip.style.setProperty('--tip-arrow',Math.max(14,Math.min(bounds.width-14,anchor.left+anchor.width/2-bounds.left))+'px');
 button.addEventListener('click',()=>tip.remove(),{once:true});
}
function openRotationSetup(recipe=null,groupChoice=null){
 if(editId!==null){showAppMessage('Save or cancel the open recipe first.');return}
 const title=recipe?'What day do you want to cook '+recipe.name+'?':'Set Up Your Rotation';
 const d=recipeBulkDialog(title);
 if(!recipe){
  const hint=document.createElement('p');hint.textContent='Pick a meal and a day. Then choose the group of recipes the app should pick from for that day.';hint.style.margin='0';d.panel.append(hint);
 }
 const tab=stage2FormField(d.panel,'Meal to plan',stage2Select(mealPlans.map(plan=>[plan.id,plan.name])));tab.value=groupChoice?.previous?.planId||activePlanId;
 const members=recipe?sharedRecipeMembers(recipe).filter(meal=>cats.includes(meal.cat)):[];
 const group=members.length>1?stage2FormField(d.panel,'Group to rotate',stage2Select([['','Choose a group'],...members.map(meal=>[meal.cat,meal.cat])])):null;
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');error.hidden=true;
 const days=document.createElement('div');days.className='recipe-bulk-fields';days.setAttribute('role','group');days.setAttribute('aria-label','Day of the week');days.style.cssText='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px';
 for(const day of orderedDays()){
  const button=document.createElement('button');button.type='button';button.className='smallbtn';button.style.cssText='min-height:44px;text-align:left';button.textContent=day;
  const showCurrentDay=()=>{button.textContent=groupChoice?.previous?.day===day&&groupChoice.previous.planId===tab.value?day+' (current day)':day};
  showCurrentDay();tab.addEventListener('change',showCurrentDay);
  button.onclick=()=>{
   const plan=mealPlans.find(plan=>plan.id===tab.value);if(!plan)return;
   if(!recipe){d.close();navigateAfterSettings(()=>{if(activePlanId!==plan.id)loadMealPlan(plan.id,false);showTop=true;allMealsActive=false;groceryTabActive=false;render();openDayCategoryPicker(day)});return}
   if(group&&!group.value){error.textContent='Choose which group to rotate.';error.hidden=false;group.focus();return}
   const meal=(group?members.find(meal=>meal.cat===group.value):members[0])||recipe,category=groupChoice?.category||meal.cat;
   try{
    const previous=groupChoice?.previous;
    const previousPlan=previous&&mealPlans.find(plan=>plan.id===previous.planId);
    if(previous&&String(previousPlan?.occasionalMeals?.[previous.day])!==String(meal.id))throw Error('The original plan has changed. Close setup and try again.');
    const keepDay=previous?.planId===plan.id&&previous.day===day;
    if(rotationWeekEntries(plan).some(entry=>entry.day===day&&!(keepDay&&entry.occasional&&(entry.meal.id===meal.id||String(entry.linkedTo)===String(meal.id)))))throw Error(day+' already has a plan. Choose another day.');
    if(category&&Object.hasOwn(plan.weekdayCategories||{},day))throw Error(day+' already has a group. Choose another day.');
    if(groupChoice)applyRecipeBulk([String(meal.id)],{category,rotation:true},{render:false,firstMealPlan:{planId:plan.id,day,category,previous,newGroup:groupChoice.newGroup}});
    else scheduleMealFromGroups(meal.id,{planId:plan.id,day,category,occasional:false,startGroup:true});
   }catch(problem){error.textContent=problem.message;error.hidden=false;return}
   d.close();navigateAfterSettings(()=>{
    if(activePlanId!==plan.id)loadMealPlan(plan.id,false);
    showTop=true;allMealsActive=false;groceryTabActive=false;render();
    showFirstRotationTip(day,category);
   });
  };days.append(button)
 }
 const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close setup');close.style.minHeight='44px';close.onclick=d.close;d.panel.append(days,error,close);tab.focus({preventScroll:true});
}
function renderEmptyMealGroups(list){
 const section=document.createElement('section');section.className='master-categories empty-meal-groups';section.setAttribute('aria-label','Meal Groups');const title=document.createElement('h2');title.textContent='Meal Groups';
 section.append(title,recipeStartActions());list.append(section);
}
function recipeStartActions(startupDialog=null){
 const actions=document.createElement('div');actions.style.cssText='display:flex;flex-wrap:wrap;gap:12px';
 const buttons=[['Import Recipes',openRecipeImportSourcePicker],['Create Recipe',()=>addRecipeToGroup('')]];
 if(startupDialog)buttons.reverse();
 for(const [label,action]of buttons){
  const button=document.createElement('button');button.type='button';button.className='smallbtn';button.textContent=label;button.style.cssText='min-height:44px;padding:10px 14px';button.onclick=()=>{startupDialog?.close();action()};
  if(startupDialog&&label==='Create Recipe')button.classList.add('first-recipe-add');
  actions.append(button);
 }
 return actions;
}
let firstRecipePromptShown=false;
function appendFirstRecipePrompt(parent){
 const title='Create or import your first recipe.';
 const launch=document.createElement('button');launch.type='button';launch.className='smallbtn first-recipe-launcher';launch.textContent=title;launch.setAttribute('aria-haspopup','dialog');
 launch.onclick=()=>{
  firstRecipePromptShown=true;
  const d=recipeBulkDialog(title,()=>launch);d.overlay.classList.add('first-recipe-dialog');
  const close=document.createElement('button');close.type='button';close.className='iconbtn first-recipe-close';setIconButton(close,'cancel','Dismiss startup prompt');close.onclick=d.close;
  const heading=d.panel.firstElementChild;heading.tabIndex=-1;
  d.panel.append(recipeStartActions(d),close);heading.focus({preventScroll:true});
 };
 parent.append(launch);
 if(!firstRecipePromptShown)requestAnimationFrame(()=>{
  if(launch.isConnected&&!firstRecipePromptShown&&!meals.length&&!document.querySelector('[aria-modal="true"]')){launch.focus({preventScroll:true});launch.click()}
 });
}
function renderMasterCategories(list){
 if(!meals.length){renderEmptyMealGroups(list);return}
 const wrap=document.createElement('section');wrap.className='master-categories';wrap.setAttribute('aria-label','Meal Groups');
 const {featuredColorById,scheduledDaysByMeal,scheduledEntries}=scheduledRecipeHighlights(null,{activePlanBadgesOnly:true});
 const hasUnassigned=meals.some(meal=>meal.cat==='');
 const heading=document.createElement('div');heading.className='master-categories-heading';
 const title=document.createElement('h2');title.textContent='Meal Groups';heading.append(title);
 const controls=document.createElement('div');controls.className='master-expansion-controls';
 const addGroup=document.createElement('button');addGroup.type='button';addGroup.className='iconbtn master-add-group';addGroup.textContent='+';addGroup.title='Add group';addGroup.setAttribute('aria-label','Add group');
 addGroup.onclick=async()=>{let n=await appDialog('New group name','','prompt');if(n&&n.trim()){try{n=createMealGroup(n)}catch(e){await showAppMessage(e.message);return}active=n;persist();const groupResult=await chooseExistingMealsForNewGroup(n.trim());if(groupResult==='delete'){cats=cats.filter(c=>c!==n.trim());active=cats[0]||'';persist();openMasterCategories()}else openMasterCategories(n.trim())}};
 for(const [expand,icon,label] of [[true,'chevrons-down','Expand all groups'],[false,'chevrons-up','Collapse all groups']]){
  const button=document.createElement('button');button.type='button';button.className='iconbtn';setIconButton(button,icon,label);
  button.onclick=()=>{masterExpansionInitialized=true;masterExpandedCategories.clear();if(expand){masterDisplayOrder().forEach(c=>masterExpandedCategories.add(c));if(hasUnassigned)masterExpandedCategories.add('')}renderList()};controls.append(button);
 }
 controls.append(addGroup);heading.append(controls);wrap.append(heading);appendRotationSetupPrompt(wrap);
 const resetOrder=document.createElement('button');resetOrder.type='button';resetOrder.className='master-order-reset';resetOrder.textContent='Reset to Weekday Order';resetOrder.hidden=!weekdayGroupOrderNeedsReset();resetOrder.onclick=()=>{if(resetWeekdayGroupOrder())renderList()};wrap.append(resetOrder);
 // With visible tabs, group headers summarize the actual recipes scheduled
 // across all tabs. With tabs hidden, retain the existing single-plan display.
 const scheduledDaysByGroup=new Map();
 if(showMealPlanTabs&&mealPlans.length>1){
  for(const entry of scheduledEntries){
   if(!scheduledDaysByGroup.has(entry.cat))scheduledDaysByGroup.set(entry.cat,new Set());
   scheduledDaysByGroup.get(entry.cat).add(entry.day);
  }
 }
 function groupHeaderColor(category){
  if(!(showMealPlanTabs&&mealPlans.length>1))return masterDisplayColor(category);
  const days=orderedDays().filter(day=>scheduledDaysByGroup.get(category)?.has(day));
  const colors=days.map(colorForDay);
  if(!colors.length)return '#ffffff';
  if(colors.length===1)return colors[0];
  return 'linear-gradient(90deg, '+colors.flatMap((color,i)=>[`${color} ${100*i/colors.length}%`,`${color} ${100*(i+1)/colors.length}%`]).join(', ')+')';
 }
 // Linked side-dish groups are active even when they are not assigned as a weekday group.
 // Preserve the normal weekday order and the user's manual order within each tier.
 const baseGroupOrder=masterDisplayOrder();
 const activeGroupNames=new Set(scheduledEntries.map(entry=>entry.cat));
 for(const entry of scheduledEntries){
  for(const targetId of (Array.isArray(entry.meal.linkedMealIds)?entry.meal.linkedMealIds:[])){
   const linked=meals.find(m=>String(m.id)===String(targetId));
   if(linked&&cats.includes(linked.cat))activeGroupNames.add(linked.cat);
  }
 }
 const displayedGroups=masterOrderedGroups([...baseGroupOrder.filter(cat=>activeGroupNames.has(cat)),...baseGroupOrder.filter(cat=>!activeGroupNames.has(cat))]);
 if(hasUnassigned)displayedGroups.unshift('');
 for(const category of displayedGroups){ 
  const categoryMeals=masterRecipeOrder(category,{scheduledEntries});
  if(!manualRecipeOrdering){
   const scheduledHere=new Set(scheduledEntries.filter(entry=>entry.planId===activePlanId&&entry.cat===category).map(entry=>sharedRecipeIdentity(entry.meal)));
   const displayRank=meal=>!meal.rotation?3:scheduledHere.has(sharedRecipeIdentity(meal))?0:scheduledDaysByMeal.has(String(meal.id))?1:2;
   // Keep the underlying queue and the order within each display tier intact.
   categoryMeals.sort((a,b)=>displayRank(a)-displayRank(b));
  }
  const card=document.createElement('section');card.className='master-category-card';card.dataset.category=category;
  const header=document.createElement('div');header.className='master-category-header';header.style.background='#f8f9fa';if(activeGroupNames.has(category)){card.classList.add('master-category-this-week');}
  const expanded=masterExpandedCategories.has(category);
  const toggle=document.createElement('button');toggle.type='button';toggle.className='master-category-title';toggle.setAttribute('aria-expanded',String(expanded));
  toggle.onclick=()=>{masterExpansionInitialized=true;const opening=!masterExpandedCategories.has(category);if(opening){if(!recipeBulkMode)masterExpandedCategories.clear();masterExpandedCategories.add(category)}else masterExpandedCategories.delete(category);if(recipeBulkMode){recipeBulkFocus={cat:category,rotation:true};bulkRecipeRender()}else renderList();if(opening&&!recipeBulkMode)requestAnimationFrame(()=>{const target=[...document.querySelectorAll('.master-category-card')].find(el=>el.dataset.category===category);if(target)target.scrollIntoView({behavior:'smooth',block:'start'});});};
  const chevron=document.createElementNS('http://www.w3.org/2000/svg','svg');chevron.setAttribute('viewBox','0 0 24 24');chevron.setAttribute('aria-hidden','true');chevron.innerHTML=expanded?'<path d="m6 15 6-6 6 6"/>':'<path d="m6 9 6 6 6-6"/>';toggle.append(chevron);
  const name=document.createElement('strong');name.textContent=category||'Unassigned';toggle.append(name);
  const count=document.createElement('span');count.className='master-category-count';count.textContent=categoryMeals.length+' '+(categoryMeals.length===1?'meal':'meals');toggle.append(count);

  header.append(toggle);
  if(category){
  const editCat=document.createElement('button');editCat.type='button';editCat.className='iconbtn';setIconButton(editCat,'rename','Edit '+category+' (reorder, rename, delete)');editCat.onclick=()=>openMasterCategoryEditMenu(category);
  header.append(editCat);
  }
  const addMeal=document.createElement('button');addMeal.type='button';addMeal.className='iconbtn';addMeal.title='Add meal to '+(category||'Unassigned');addMeal.setAttribute('aria-label',addMeal.title);addMeal.textContent='+';addMeal.style.cssText='font-size:24px';
  addMeal.disabled=addingGroupRecipe||newRecipeDraftId!==null;addMeal.onclick=()=>addRecipeToGroup(category);
  header.append(addMeal);
  card.append(header);
  if(expanded){
   const items=document.createElement('div');items.className='master-category-meals';
   for(const [label,rot] of category?[['In Rotation',true],['Ideas',false]]:[['Recipes',false]]){
    const groupMeals=category?categoryMeals.filter(m=>!!m.rotation===rot):categoryMeals;
    const section=document.createElement('div');section.className='master-recipe-section';section.dataset.recipeSection=rot?'rotation':'ideas';
    const open=!category||masterRecipeSectionOpen(category,rot),bodyId='master-section-'+cats.indexOf(category)+'-'+section.dataset.recipeSection;
    const group=document.createElement('button');group.type='button';group.className='master-category-group-label';group.setAttribute('aria-expanded',String(open));group.setAttribute('aria-controls',bodyId);group.setAttribute('aria-label',category+': '+label+' ('+groupMeals.length+' recipes)');
    const chevron=document.createElementNS('http://www.w3.org/2000/svg','svg');chevron.setAttribute('viewBox','0 0 24 24');chevron.setAttribute('aria-hidden','true');chevron.innerHTML='<path d="'+(open?'m6 15 6-6 6 6':'m6 9 6 6 6-6')+'"/>';
    const sectionName=document.createElement('span');sectionName.className='master-recipe-section-name';sectionName.textContent=label;
    const sectionCount=document.createElement('span');sectionCount.className='master-recipe-section-count';sectionCount.textContent=String(groupMeals.length);group.append(chevron,sectionName,sectionCount);
    group.onclick=e=>{e.preventDefault();e.stopPropagation();setMasterRecipeSectionOpen(category,rot,!masterRecipeSectionOpen(category,rot));if(recipeBulkMode){recipeBulkFocus={cat:category,rotation:rot};bulkRecipeRender()}else renderList();document.getElementById(bodyId)?.previousElementSibling?.focus({preventScroll:true})};
    const sectionBody=document.createElement('div');sectionBody.className='master-recipe-section-recipes';sectionBody.id=bodyId;sectionBody.hidden=!open;if(category)section.append(group);section.append(sectionBody);items.append(section);
    for(const m of groupMeals){
     const row=document.createElement('div');row.className='master-category-meal';row.dataset.mealId=String(m.id);const manualMoves=[];if(featuredColorById.has(String(m.id))){row.style.backgroundColor=featuredColorById.get(String(m.id));row.style.borderRadius='8px';row.classList.add('featured-top-meal')}bindMealSwipe(row,m);
     if(rot&&manualRecipeOrdering){for(const [glyph,dir] of [['↑',-1],['↓',1]]){const btn=document.createElement('button');btn.type='button';btn.className='move';btn.textContent=glyph;btn.title=(dir<0?'Up':'Down')+': tap to move to '+(dir<0?'top':'bottom')+', hold to move one position';bindMasterCategoryMove(btn,m,dir);manualMoves.push(btn)}}

     const name=document.createElement('button');name.type='button';name.className='master-category-meal-name';name.textContent=m.name||'Untitled meal';bindGroupMealPress(name,m);const mealInfo=document.createElement('div');mealInfo.className='master-meal-info';const nameLine=document.createElement('div');nameLine.className='shared-meal-name-line';nameLine.append(name);const sharedCopies=m.linkGroup?meals.filter(x=>x.linkGroup===m.linkGroup&&x.id!==m.id):[];if(sharedCopies.length){const sharedButton=document.createElement('button');sharedButton.type='button';sharedButton.className='shared-meal-link-button';sharedButton.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.1 0l3-3a5 5 0 0 0-7.1-7.1l-1.7 1.7M14 11a5 5 0 0 0-7.1 0l-3 3a5 5 0 0 0 7.1 7.1l1.7-1.7"/></svg>';sharedButton.title='View other groups containing this recipe';sharedButton.setAttribute('aria-label','View groups sharing '+(m.name||'this recipe'));sharedButton.onclick=e=>{e.preventDefault();e.stopPropagation();showSharedRecipeGroups(m)};nameLine.append(sharedButton)}
     const hasOutgoing=Array.isArray(m.linkedMealIds)&&m.linkedMealIds.some(id=>meals.some(other=>String(other.id)===String(id)));
     const hasIncoming=meals.some(other=>other!==m&&Array.isArray(other.linkedMealIds)&&other.linkedMealIds.some(id=>String(id)===String(m.id)));
     if(hasIncoming&&!hasOutgoing){const fullName=String(m.name||'Untitled meal');const lastSpace=fullName.lastIndexOf(' ');if(lastSpace>0){name.textContent=fullName.slice(0,lastSpace);nameLine.append(document.createTextNode(' '));const ending=document.createElement('span');ending.className='linked-name-ending';const lastWord=document.createElement('button');lastWord.type='button';lastWord.className='master-category-meal-name';lastWord.textContent=fullName.slice(lastSpace+1);bindGroupMealPress(lastWord,m);ending.append(lastWord);nameLine.append(ending)}const relatedButton=document.createElement('button');relatedButton.type='button';relatedButton.className='related-meal-indicator';relatedButton.textContent='↗';relatedButton.title='View linked meals';relatedButton.setAttribute('aria-label','View meals linked to '+(m.name||'this recipe'));relatedButton.onclick=e=>{e.preventDefault();e.stopPropagation();showRelatedMeals(m)};if(lastSpace>0){nameLine.lastElementChild.append(relatedButton)}else{nameLine.append(relatedButton)}}if(m.needsTweaking===true){let ending=nameLine.querySelector('.linked-name-ending'),lastName=ending?.querySelector('.master-category-meal-name')||name;const text=String(m.name||'Untitled meal'),space=text.lastIndexOf(' ');if(!ending&&space>0){name.textContent=text.slice(0,space);ending=document.createElement('span');ending.className='linked-name-ending';lastName=document.createElement('button');lastName.type='button';lastName.className='master-category-meal-name';lastName.textContent=text.slice(space+1);bindGroupMealPress(lastName,m);ending.append(lastName);name.after(document.createTextNode(' '),ending)}lastName.after(needsTweakingIndicator(m))}bindRecipeTimerName(nameLine.querySelector('.linked-name-ending .master-category-meal-name')||name,m,m.favorite===true&&!hasIncoming);mealInfo.append(nameLine);appendMealTimes(mealInfo,m,true);appendLastCookedLabel(mealInfo,m);
     if(Array.isArray(m.linkedMealIds)&&m.linkedMealIds.length){
      const linkedTargets=[...new Map(m.linkedMealIds.map(targetId=>meals.find(x=>String(x.id)===String(targetId))).filter(Boolean).map(target=>[String(target.id),target])).values()];
      if(linkedTargets.length){
       const linkedInfo=document.createElement('div');linkedInfo.className='top-inline-linked';linkedInfo.style.cssText='font-size:13px;color:#637080;margin-top:2px;display:flex;flex-wrap:wrap;gap:2px 7px;align-items:center';
       
       linkedTargets.forEach((target,index)=>{
        if(index){const sep=document.createElement('span');sep.textContent='·';linkedInfo.append(sep)}
        const link=document.createElement('button');link.type='button';link.textContent=target.name||'Untitled meal';link.title='Meal options for '+(target.name||'meal');link.style.cssText='background:none;border:0;padding:0;color:inherit;font:inherit;text-decoration:none;cursor:pointer;text-align:left';
        link.onclick=e=>{e.preventDefault();e.stopPropagation();openTopMealActionMenu(null,target.cat,target,true)};
        linkedInfo.append(link);bindRecipeTimerName(link,target,false);appendNeedsTweakingIndicator(linkedInfo,target)
       });mealInfo.append(linkedInfo)
      }
     }
     if(!category&&meals.length===1&&newRecipeDraftId===null){
      const planned=scheduledEntries.find(entry=>entry.meal.id===m.id&&entry.occasional&&!entry.linkedTo);
      const planRecipe=document.createElement('button');planRecipe.type='button';planRecipe.className='smallbtn';planRecipe.style.minHeight='44px';planRecipe.textContent=planned?'Choose a group for rotation':'Add to weekly plan';
      planRecipe.onclick=()=>chooseGroupForFirstMeal(m,planned?{day:planned.day,planId:planned.planId}:null);
      mealInfo.append(planRecipe);
     }
     row.append(mealInfo,...manualMoves);
     if(category)row.append(recipeSectionMoveButton(m));bindRecipeBulkRow(row,m);
     appendScheduledRecipeWeekdays(row,m,scheduledDaysByMeal);
     
     sectionBody.append(row);
    }
   }
   card.append(items);
  }
  wrap.append(card);
 }
 if(!cats.length&&!hasUnassigned){const empty=document.createElement('div');empty.textContent='No groups yet. Tap + to add one.';wrap.append(empty)}
 list.append(wrap);if(recipeBulkMode)updateRecipeBulkUI();else installMasterGroupDragging(wrap,resetOrder);
}
function renderList(){if(recipeBulkMode&&(showTop||editId!==null))endRecipeBulk();masterGroupDragCleanup?.();masterGroupDragCleanup=null;reconcileActiveLinkedMeals();rememberCurrentView();
 if(isOnboardingZeroState()){renderOnboardingWelcome();return}
 if(lowerSettingsVisible){
  const old=document.getElementById('planSettingsPanel');
  if(old)lowerOpenGroups=new Set([...old.querySelectorAll('details[data-settings-group][open]')].map(d=>d.dataset.settingsGroup));
 }
 document.body.classList.toggle('overview-without-category-pins',showTop&&(allMealsActive||groceryTabActive));resetGroceriesForNewTopMeals();document.querySelectorAll('.add-meal-floating').forEach(b=>b.remove());persist();let list=$('list');const categoryRow=document.getElementById('categoryButtons');if(categoryRow&&categoryRow.parentNode!==$('tabs'))$('tabs').append(categoryRow);const editorEl=$('editor');if(editorEl&&list.contains(editorEl))document.body.insertBefore(editorEl,list);list.classList.toggle('top-summary',showTop);list.innerHTML='';if(!showTop){groceryTabActive=false;allMealsActive=false;topPanel.classList.add('hidden');addFloatingViewButtons()}if(showTop){if(showTop&&showMealPlanTabs){
 const tabBar=document.createElement('div');tabBar.className='meal-plan-tabs';tabBar.setAttribute('role','tablist');tabBar.setAttribute('aria-label','Meal plans');
 for(const plan of mealPlans){
  const tab=document.createElement('div');tab.className='meal-plan-tab'+(plan.id===activePlanId&&!groceryTabActive&&!allMealsActive?' selected':'');
  const name=document.createElement('button');name.type='button';name.className='meal-plan-tab-name';name.textContent=plan.name;name.setAttribute('role','tab');name.setAttribute('aria-selected',String(plan.id===activePlanId&&!groceryTabActive&&!allMealsActive));
  name.onclick=()=>{if(plan.id!==activePlanId)navigateAfterSettings(()=>loadMealPlan(plan.id));else if(groceryTabActive||allMealsActive)navigateAfterSettings(()=>{groceryTabActive=false;allMealsActive=false;renderList()})};
  // Open tab editing as soon as the hold threshold is reached. On touch
  // devices a contextmenu/click may also fire; suppress both after a hold.
  let hold=null,held=false,pressStart=null;
  const openTabEditor=()=>{
   menuCat=null;renderMenu();
   if(plan.id!==activePlanId){
    navigateAfterSettings(()=>{loadMealPlan(plan.id);activeTabMenuId=plan.id;renderList()});
   }else{activeTabMenuId=plan.id;renderList()}
  };
  name.style.touchAction='pan-x';
  name.addEventListener('pointerdown',e=>{
   if(e.pointerType==='mouse'&&e.button!==0)return;
   clearTimeout(hold);held=false;pressStart={x:e.clientX,y:e.clientY};
   hold=setTimeout(()=>{hold=null;held=true;openTabEditor()},550);
  });
  name.addEventListener('pointermove',e=>{
   if(pressStart&&Math.hypot(e.clientX-pressStart.x,e.clientY-pressStart.y)>12){clearTimeout(hold);hold=null;pressStart=null}
  });
  ['pointerup','pointercancel','pointerleave'].forEach(ev=>name.addEventListener(ev,()=>{clearTimeout(hold);hold=null;pressStart=null}));
  name.addEventListener('click',e=>{if(held){e.stopImmediatePropagation();e.preventDefault();held=false}},true);
  name.oncontextmenu=e=>{e.preventDefault();if(!held){clearTimeout(hold);hold=null;held=true;openTabEditor()}};
  tab.append(name);tabBar.append(tab);

 }
 const add=document.createElement('button');add.type='button';add.className='meal-plan-add';add.textContent='+';add.onclick=openAddMealTabDialog;add.setAttribute('aria-label','Add meal tab');add.title='Add meal tab';add.style.minWidth=add.style.minHeight='44px';tabBar.append(add);
 list.append(tabBar);
 if(splitPlanSettings()&&categoryRow)tabBar.after(categoryRow);
 if(activeTabMenuId&&mealPlans.some(p=>p.id===activeTabMenuId)){
  const menu=document.createElement('div');menu.className='catmenu meal-plan-menu';
  const selected=mealPlans.find(p=>p.id===activeTabMenuId);
  function arrow(direction,label){
   const b=document.createElement('button');b.className='arrow iconbtn';b.title=label;b.setAttribute('aria-label',label);
   b.innerHTML=direction<0?'<svg viewBox="0 0 24 24"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>':'<svg viewBox="0 0 24 24"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>';
   b.onclick=()=>{const i=mealPlans.findIndex(p=>p.id===selected.id),j=i+direction;if(j<0||j>=mealPlans.length)return;snapshot();[mealPlans[i],mealPlans[j]]=[mealPlans[j],mealPlans[i]];saveActiveMealPlan();renderList()};menu.append(b);
  }
  arrow(-1,'Move tab left');arrow(1,'Move tab right');
  async function rename(){
   const next=await appDialog('Rename meal plan',selected.name,'prompt');
   if(next&&next.trim()){snapshot();selected.name=next.trim();saveActiveMealPlan();activeTabMenuId=null;renderList()}
  }
  async function remove(){
   if(mealPlans.length===1){await showAppMessage('Keep at least one meal plan.');return}
   if(!await appDialog('Delete meal plan “'+selected.name+'”? Recipes will be kept.',null,'yesno'))return;
   snapshot();saveActiveMealPlan();mealPlans=mealPlans.filter(p=>p.id!==selected.id);
   activeTabMenuId=null;
   if(activePlanId===selected.id){
    const plan=mealPlans[0];activePlanId=plan.id;
    weekdayCategories=JSON.parse(JSON.stringify(plan.weekdayCategories));weekdayMealOverrides={...(plan.weekdayMealOverrides||{})};autoPinTopCategories=true;
   }
   saveActiveMealPlan();render();
  }
  for(const [title,type,action] of [['Rename','rename',rename],['Delete','delete',remove],['Cancel','cancel',()=>{activeTabMenuId=null;renderList()}]]){
   const b=document.createElement('button');b.className='smallbtn';setIconButton(b,type,title);b.onclick=action;menu.append(b);
  }
  tabBar.after(menu);
 }
}
 if(!allMealsActive&&!groceryTabActive&&rotationWeekOffset){renderRotationWeekPreview(list);addFloatingViewButtons();return;}
 if(groceryTabActive){renderGroceryViewToolbar(list);renderMasterGroceryTab(list);addFloatingViewButtons();return;}
const showRotationActions=!allMealsActive&&!groceryTabActive&&(
 mealPlans.some(plan=>Object.keys(plan.id===activePlanId?weekdayCategories:plan.weekdayCategories||{}).length)||
 getDisplayedWeekdayMeals().length>0||!!readPreviousRotation()
);
const topControls=document.createElement('div');topControls.className='top-controls';topControls.style.cssText='display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:4px 2px 12px;color:#555';const iconButton=(title,svg,action)=>{const b=document.createElement('button');b.type='button';b.className='iconbtn top-action-icon';b.title=title;b.setAttribute('aria-label',title);b.innerHTML=svg;b.onclick=action;b.style.cssText='width:36px;height:36px;border:0!important;padding:4px!important;display:grid;place-items:center;color:#555';topControls.append(b);return b};const svg=(paths)=>'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="'+paths+'" stroke-linecap="round" stroke-linejoin="round"/></svg>';if(showRotationActions){const moveDownButton=iconButton('Rotate out recipes','<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v12m-5-5 5 5 5-5M5 20h14" stroke-linecap="round" stroke-linejoin="round"/></svg>',()=>openRotateOptions());let moveHoldTimer=null,moveHoldTriggered=false,movePressStart=0;moveDownButton.style.touchAction='manipulation';moveDownButton.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse'&&e.button!==0)return;clearTimeout(moveHoldTimer);moveHoldTriggered=false;movePressStart=Date.now();moveHoldTimer=setTimeout(()=>{moveHoldTriggered=true},450)});['pointerup','pointerleave','pointercancel'].forEach(ev=>moveDownButton.addEventListener(ev,()=>clearTimeout(moveHoldTimer)));moveDownButton.addEventListener('contextmenu',e=>e.preventDefault());moveDownButton.addEventListener('click',e=>{const longPress=moveHoldTriggered||(movePressStart&&Date.now()-movePressStart>=450);moveHoldTriggered=false;movePressStart=0;if(longPress){e.preventDefault();e.stopImmediatePropagation()}},true);iconButton('Rotate all meals back to before the last rotation','<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20V8m-5 5 5-5 5 5M5 4h14" stroke-linecap="round" stroke-linejoin="round"/></svg>',openRotateBackOptions);const moveBackButton=topControls.lastElementChild;[moveDownButton,moveBackButton].forEach(button=>{button.classList.add('rotation-standalone-action');button.style.cssText='width:36px;height:36px;border:0!important;background:transparent!important;padding:4px!important;display:grid;place-items:center;color:#555'});}appendMealPlanSettingsGear(topControls);
if(!allMealsActive&&!groceryTabActive){
 const pageHeading=document.createElement('h2');
 pageHeading.className='view-page-title';
 const tabName=mealPlans.find(plan=>plan.id===activePlanId)?.name?.trim();
 pageHeading.textContent=tabName?`My ${tabName} Rotation`:'My Rotation';
 list.append(pageHeading);
 appendOnboardingHint(list);
 if(!meals.length)appendFirstRecipePrompt(list);
}
list.append(topControls);placeViewToolbar(topControls);
if(!allMealsActive&&!groceryTabActive){const heading=list.querySelector(':scope > .view-page-title');if(heading){const header=document.createElement('div');header.className='rotation-compact-header';header.append(heading,rotationWeekControls([...topControls.querySelectorAll('.rotation-standalone-action')]));topControls.after(header)}}
if(!allMealsActive&&!groceryTabActive)appendRotationSetupPrompt(list);
appendMealPlanSettingsPanel(list);
if(allMealsActive){renderAllMealsOverview(list);addFloatingViewButtons();return;}
addFloatingViewButtons();renderTodayTodo();

 const displayedTop=getDisplayedWeekdayMeals(),currentPlan=mealPlans.find(p=>p.id===activePlanId),temporarySlots=weekSchedule(currentPlan).slots;
for(const day of orderedDays()){
 const assigned=getDayCategories(day);
 if(!assigned.length&&!displayedTop.some(item=>item.day===day))displayedTop.push({day,cat:null,meal:null});
 // The planner returns real meals only. Keep every assigned group visible when
 // some groups have no eligible recipe, even if another group already has one.
 if(!temporarySlots[temporarySlotKey(day,null)])for(const cat of assigned){
  if(!displayedTop.some(item=>item.day===day&&item.cat===cat)&&!temporarySlots[temporarySlotKey(day,cat)])displayedTop.push({day,cat,meal:null,needsRotation:true});
 }
}
for(const entry of emptyWeekEntries(currentPlan)){
 const assigned=getDayCategories(entry.day),independent=getDisplayedWeekdayMealsForPlan(currentPlan,null,null,null,true).some(item=>item.day===entry.day&&item.cat===entry.cat&&item.occasional&&item.linkedTo==null);
 if(entry.cat!=='@day'&&!assigned.includes(entry.cat)&&!independent)continue;
 for(let i=displayedTop.length-1;i>=0;i--)if(displayedTop[i].day===entry.day&&!displayedTop[i].meal&&!displayedTop[i].temporaryEmpty&&(entry.cat==='@day'||displayedTop[i].cat===entry.cat||displayedTop[i].cat==null))displayedTop.splice(i,1);
 displayedTop.push({...entry,meal:null,temporaryEmpty:true});
}
const dayOrder=orderedDays(),displayPlan=mealPlans.find(p=>p.id===activePlanId),underlyingDisplay=displayPlan.weekSchedule?queueWeekEntries(displayPlan):null;const assignedRank=entry=>{const index=getDayCategories(entry.day).indexOf(entry.cat);return index<0?cats.length:index};
const orderedRank=entry=>weekDisplayRank(displayPlan,entry.meal?entry:{...entry,meal:{id:''}},underlyingDisplay);
displayedTop.sort((a,b)=>dayOrder.indexOf(a.day)-dayOrder.indexOf(b.day)||(underlyingDisplay&&weekSchedule(displayPlan).order[a.day]?.length?orderedRank(a)-orderedRank(b):assignedRank(a)-assignedRank(b)));
// Linked recipes without a manually assigned second group appear beneath
// their parent recipe, rather than occupying an additional weekday slot.
const inlineLinkedByParent=new Map();
for(let i=displayedTop.length-1;i>=0;i--){
 const entry=displayedTop[i];
 if(!entry.meal||!entry.linkedTo||getDayCategories(entry.day).includes(entry.cat))continue;
 const parent=displayedTop.find(other=>other.day===entry.day&&other.meal&&String(other.meal.id)===String(entry.linkedTo));
 if(!parent)continue;
 const key=entry.day+'|'+String(parent.meal.id);
 if(!inlineLinkedByParent.has(key))inlineLinkedByParent.set(key,[]);
 inlineLinkedByParent.get(key).unshift(entry.meal);
 displayedTop.splice(i,1);
}
const mealSlotsByDay={};
for(const item of displayedTop)mealSlotsByDay[item.day]=(mealSlotsByDay[item.day]||0)+1;
let previousRenderedDay=null;
const renderedSlotsByDay={};
displayedTop.forEach(entry=>{
 const {day,cat:c,meal:top,needsRotation,linkedTo,temporaryEmpty}=entry;
 renderedSlotsByDay[day]=(renderedSlotsByDay[day]||0)+1;const lastSlot=renderedSlotsByDay[day]===mealSlotsByDay[day];
  if(day!==previousRenderedDay){
    const dayHeading=document.createElement('button');dayHeading.type='button';dayHeading.className='section weekday-heading';dayHeading.dataset.weekday=day;dayHeading.textContent=day;
    dayHeading.style.cursor='pointer';dayHeading.title='Choose meal group for '+day;
    dayHeading.setAttribute('role','button');dayHeading.tabIndex=0;
    dayHeading.onclick=e=>{e.preventDefault();e.stopPropagation();openWeekdayCard(day)};
    dayHeading.style.background=colorForDay(day);
    dayHeading.style.borderRadius='8px 8px 0 0';dayHeading.style.padding='9px 12px';
    list.append(dayHeading);
    previousRenderedDay=day;
  }
if(!top){
 const blank=document.createElement('div');blank.className='empty-weekday-meal';blank.dataset.scheduleDay=day;blank.dataset.category=c||'';blank.dataset.weekRow='true';blank.dataset.displayKey=scheduleDisplayKey(entry);
 blank.setAttribute('role','button');blank.tabIndex=0;blank.setAttribute('aria-label',day+(c&&c!=='@day'?' '+c:'')+(temporaryEmpty?' empty this week':' no meal planned'));
 const line=document.createElement('div');line.className='top-meal-title-line';const message=document.createElement('span');message.className='mealname';message.textContent='—';line.append(message);
 if(c&&c!=='@day'){const tag=document.createElement('span');tag.textContent=c;tag.className='top-meal-category top-meal-inline-category';line.append(tag)}
 const open=()=>temporaryEmpty?openWeekEmptyActions(day,c):!getDayCategories(day).length?openWeekdayCard(day):c?openUnscheduledGroupActions(day,c):openDayCategoryPicker(day);
 blank.onclick=()=>open();blank.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}};
 blank.style.cssText='background:'+colorForDay(day)+';padding:3px 16px 3px 14px;min-height:40px;color:#777;border-radius:'+(lastSlot?'0 0 8px 8px':'0');blank.append(line);
 bindWeekMealGestures(blank,blank,day,entry,()=>{});list.append(blank);return;
}
let row=document.createElement('div');row.className='meal';if(mealSlotsByDay[day]>1)row.classList.add('multi-category-meal');row.dataset.mealId=String(top.id);if(!top.temporaryMeal)bindMealSwipe(row,top);let body=document.createElement('div');body.className='mealbody';let name=document.createElement('button');name.className='mealname';name.textContent=top.name;name.style.userSelect='none';name.style.webkitUserSelect='none';name.style.webkitTouchCallout='none';name.style.touchAction='pan-y';name.addEventListener('selectstart',e=>e.preventDefault());// Tap for meal options; hold for the saved recipe link.
const openMealRecipe=()=>openSavedMealRecipe(top,cookingContext(activePlanId,day,c,top,linkedTo));
name.onclick=()=>openTopMealActionMenu(day,c,top,false,cookingContext(activePlanId,day,c,top,linkedTo));

const mealTitleLine=document.createElement('div');mealTitleLine.className='top-meal-title-line';
if(top.needsTweaking===true){const line=document.createElement('span');line.className='recipe-name-with-tweak';line.append(name,needsTweakingIndicator(top));mealTitleLine.append(line)}else mealTitleLine.append(name);bindRecipeTimerName(name,top,linkedTo==null&&!getDisplayedWeekdayMeals().some(parent=>parent.day===day&&parent.meal.id!==top.id&&(parent.meal.linkedMealIds||[]).some(id=>String(id)===String(top.id))));
if(c&&cats.includes(c)){
 const displayGroup=pairedMainGroup(mealPlans.find(plan=>plan.id===activePlanId),day,c)?top.cat:c;const tag=document.createElement('button');tag.type='button';tag.textContent=displayGroup;tag.className='top-meal-category clickable-group-heading top-meal-inline-category';
 tag.title='Open '+displayGroup+' in Meal Groups';tag.setAttribute('aria-label','Open '+displayGroup+' group in Meal Groups');
 tag.onclick=e=>{e.preventDefault();e.stopPropagation();navigateAfterSettings(()=>openMasterCategories(displayGroup))};
 mealTitleLine.append(tag);
}
body.append(mealTitleLine);
const inlineLinked=inlineLinkedByParent.get(day+'|'+String(top.id))||[];
if(inlineLinked.length){
 const linkedInfo=document.createElement('div');
 linkedInfo.className='top-inline-linked';linkedInfo.style.cssText='font-size:13px;color:#637080;margin-top:1px;display:flex;flex-wrap:wrap;gap:2px 7px;align-items:center;line-height:1.2';

 inlineLinked.forEach((target,index)=>{
  if(index){const sep=document.createElement('span');sep.textContent='·';linkedInfo.append(sep)}
  const link=document.createElement('button');link.type='button';link.textContent=target.name;
  link.title='Meal options for '+target.name;
  link.style.cssText='border:0;background:transparent;color:inherit;text-decoration:none;padding:0;font:inherit;cursor:pointer;text-align:left';
  link.onclick=e=>{e.preventDefault();e.stopPropagation();openTopMealActionMenu(day,target.cat,target,false,cookingContext(activePlanId,day,target.cat,target,top.id))};
  linkedInfo.append(link);bindRecipeTimerName(link,target,false);appendNeedsTweakingIndicator(linkedInfo,target);
 });
 body.append(linkedInfo);
}
appendMealTimes(body,top);for(const side of getDayCategories(day)){const plan=mealPlans.find(p=>p.id===activePlanId);if(!weekSchedule(plan).slots[temporarySlotKey(day,side)]&&pairedMainGroup(plan,day,side)===c&&!getDisplayedWeekdayMeals().some(entry=>entry.day===day&&entry.cat===side)&&!displayedTop.some(entry=>entry.day===day&&entry.cat===side&&!entry.meal)){const message=document.createElement('button');message.type='button';message.className='times';message.textContent=side+': no matching side in rotation';message.setAttribute('aria-label','Choose '+day+"'s "+side+' meal');message.style.cssText='display:block;border:0;background:transparent;padding:4px 0;min-height:44px;text-align:left;color:var(--muted,#777);font:inherit;font-size:12px;text-decoration:underline;text-underline-offset:2px';message.onclick=e=>{e.preventDefault();e.stopPropagation();openWeekdayMealChooser(day,side,null)};body.append(message)}}row.append(body);const wrap=document.createElement('div');wrap.className='top-recipe-wrap';wrap.style.background=colorForDay(day);wrap.style.borderRadius=lastSlot?'0 0 8px 8px':'0';wrap.dataset.weekRow='true';wrap.dataset.scheduleDay=day;wrap.dataset.displayKey=scheduleDisplayKey(entry);bindWeekMealGestures(row,name,day,entry,openMealRecipe);wrap.append(row);if(!getDayCategories(day).length){wrap.style.cursor='pointer';wrap.onclick=e=>{if(!e.defaultPrevented&&!e.target.closest('button,input,select,a'))openWeekdayCard(day)}}list.append(wrap)});return}if(!showTop){renderMasterCategories(list);return}if(!active)return;const featuredColorById=new Map();for(const entry of getDisplayedWeekdayMealsForPlan(masterDisplayPlan())){if(!featuredColorById.has(String(entry.meal.id)))featuredColorById.set(String(entry.meal.id),colorForDay(entry.day))} [['IN ROTATION',true],['IDEAS',false]].forEach(([title,rot])=>{let h=document.createElement('div');h.className='section';h.textContent=title;list.append(h);masterRecipeOrder(active).filter(m=>m.rotation===rot).forEach(m=>{let row=document.createElement('div');row.className='meal';row.dataset.mealId=String(m.id);if(featuredColorById.has(String(m.id))){row.style.backgroundColor=featuredColorById.get(String(m.id));row.style.borderRadius='8px';row.classList.add('featured-top-meal')}bindMealSwipe(row,m);if(rot&&manualRecipeOrdering){let up=document.createElement('button');up.className='move';up.textContent='↑';up.title='Tap: move to top; long press: move up one';up.setAttribute('aria-label','Move '+(m.name||'meal')+' up');function bindMoveArrow(btn,dir){let holdTimer=null,held=false;btn.addEventListener('pointerdown',()=>{held=false;holdTimer=setTimeout(()=>{held=true;const group=meals.filter(x=>x.cat===m.cat&&x.rotation);const pos=group.findIndex(x=>x.id===m.id),target=pos+dir;if(pos<0||target<0||target>=group.length)return;snapshot();const other=group[target],a=meals.indexOf(m),b=meals.indexOf(other);if(a>=0&&b>=0){meals[a]=other;meals[b]=m;clearOverridesForCat(m.cat);persist();renderList()}},500)});['pointerup','pointerleave','pointercancel'].forEach(ev=>btn.addEventListener(ev,()=>clearTimeout(holdTimer)));btn.onclick=()=>{if(held){held=false;return}moveMasterCategoryMeal(m,dir,false)}}bindMoveArrow(up,-1);row.append(up);let down=document.createElement('button');down.className='move';down.textContent='↓';down.title='Tap: move to bottom; long press: move down one';down.setAttribute('aria-label','Move '+(m.name||'meal')+' down');bindMoveArrow(down,1);row.append(down)}else if(!rot){let cb=document.createElement('input');cb.type='checkbox';cb.className='check';cb.setAttribute('aria-label','Add to rotation');cb.onchange=()=>{if(cb.checked)promoteMealToRotation(m)};row.append(cb)}let body=document.createElement('div');body.className='mealbody';let name=document.createElement('button');name.className='mealname';name.textContent=m.name;name.style.userSelect='none';name.style.webkitUserSelect='none';name.style.webkitTouchCallout='none';name.style.touchAction='pan-y';name.addEventListener('selectstart',e=>e.preventDefault());name.onclick=e=>{if(m.url){e.preventDefault();window.open(m.url,'_blank','noopener')}};bindRenameLongPress(name,m);name.oncontextmenu=e=>e.preventDefault();body.append(name);bindRecipeTimerName(name,m);appendNeedsTweakingIndicator(body,m);appendMealTimes(body,m);row.append(body);if(m.linkGroup&&meals.filter(x=>x.linkGroup===m.linkGroup).length>1){const dot=document.createElement('span');dot.className='linked-meal-dot';dot.textContent='•';dot.title='Shared across groups';dot.setAttribute('aria-label','Shared across groups');dot.style.cssText='margin-left:auto;padding:0 9px;font-size:23px;color:#6a7484;flex:0 0 auto';row.append(dot)}list.append(row)})});let add=document.createElement('button');add.className='smallbtn add-meal-floating';add.textContent='+';add.title='Add meal';add.setAttribute('aria-label','Add meal');add.onclick=()=>{snapshot();let m={id:id++,cat:active,name:'',rotation:false,prep:'',cook:'',total:'',url:''};meals.push(m);openEditor(m.id)};document.body.append(add)}function openLinkedMealEditorInline(meal,navigationOrigin=null){openEditor(meal.id,false,navigationOrigin)}
// Undo restores only the removed occurrence and its linked cooking contexts.
// Progress made on retained meals after Skip must remain untouched.
function captureSkippedCookingState(plan,entry){
 const matches=c=>c&&String(c.planId)===String(plan.id)&&c.day===entry.day;
 const sessions=Object.fromEntries(Object.entries(cookingSessions.occurrences).filter(([,v])=>matches(v.context))),scales=Object.fromEntries(Object.entries(occurrenceScales.occurrences).filter(([,v])=>matches(v.context)));
 return JSON.parse(JSON.stringify({keys:[rotationOccurrenceKey({...entry,planId:plan.id})],sessions,scales}));
}
function finishSkippedCookingUndo(undo){
 const saved=undo.skippedCookingState;
 for(const [prior,current]of [[saved.sessions,cookingSessions.occurrences],[saved.scales,occurrenceScales.occurrences]])for(const key of Object.keys(prior))if(!current[key])saved.keys.push(key);
 saved.keys=[...new Set(saved.keys)];
 // Skip is synchronous after choosing an alternative; refine that one Undo entry.
 history[history.length-1]=JSON.stringify(undo);
}
function restoreSkippedCookingState(saved){
 if(!Array.isArray(saved?.keys))return;
 for(const key of saved.keys){for(const [target,prior]of [[cookingSessions.occurrences,saved.sessions],[occurrenceScales.occurrences,saved.scales]]){if(prior?.[key])target[key]=JSON.parse(JSON.stringify(prior[key]));else delete target[key]}}
 writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales);
}

// A local schedule substitution: no queue movement, cooking event or week advance.
async function skipScheduledMeal(day,category,meal){
 if(groceryCheckStorageInvalid){await showAppMessage('Saved grocery selections could not be read. No meal was changed.');return false}
 saveActiveMealPlan();const plan=mealPlans.find(p=>p.id===activePlanId),schedules=new Map(mealPlans.map(p=>[p.id,getDisplayedWeekdayMealsForPlan(p)])),prior=schedules.get(plan.id)||[];
 const current=prior.find(item=>item.day===day&&item.cat===category&&String(item.meal.id)===String(meal.id));
 if(!current||!rotationGroupScheduled(plan,day,category)||current.occasional){await showAppMessage('This meal has no independent assigned group. Change the one-time meal or skip its parent meal instead.');return false}
 const key=weekdaySlotKey(day,category),excluded=new Set([String(meal.id)]);
 // A replacement must not consume another meal displaced earlier this week.
 for(const choice of Object.values(plan.cycleSlotChoices||{}))for(const id of choice.deferredMealIds||[])excluded.add(String(id));
 const possible=automaticSlotCandidates(plan,day,category,meals,prior).filter(m=>!excluded.has(String(m.id)));
 if(!possible.length){await showAppMessage('No alternative eligible recipe is available. This meal has been kept.');return false}
 const grocery=captureGroceryCheckStates(),used=new Set([...schedules.values()].flat().filter(item=>item!==current).map(item=>String(item.meal.id)));
 const skipUndo={...JSON.parse(captureState()),skippedCookingState:captureSkippedCookingState(plan,current)};snapshot(JSON.stringify(skipUndo));
 // Skipping is a schedule edit, not a consumed weighted rotation turn.
 const ranked=automaticSlotCandidates(plan,day,category,meals,prior).filter(m=>!excluded.has(String(m.id))),next=ranked.find(m=>!used.has(String(m.id)))||ranked[0];
 preserveOtherMealPlanChoices(null,null,schedules);
 // Fix unrelated days/tabs even when the only alternative is already scheduled.
 for(const other of mealPlans)for(const entry of schedules.get(other.id)||[]){if(other.id===plan.id&&entry.day===day)continue;const slot=weekdaySlotKey(entry.day,entry.cat),choice=other.cycleSlotChoices?.[slot];if(choice)choice.retain=true}
 const blocked=prior.filter(item=>item.day===day&&item!==current&&(item.meal.linkedMealIds||[]).some(id=>String(id)===String(meal.id))).map(item=>String(item.meal.id));
 plan.weekdayMealOverrides={...plan.weekdayMealOverrides,[key]:String(next.id)};plan.cycleRetainedSlots={...plan.cycleRetainedSlots,[key]:String(next.id)};
 plan.cycleSlotChoices={...plan.cycleSlotChoices,[key]:{mealId:String(next.id),parentId:'',skipReplacement:true,deferredMealIds:[...new Set([...(plan.cycleSlotChoices?.[key]?.deferredMealIds||[]),String(meal.id)])],avoidMealId:String(meal.id),excludedMealIds:[...excluded],blockedParents:blocked}};
 weekdayMealOverrides={...plan.weekdayMealOverrides};
 const affected=cycleAffectedEntries(prior,[current],plan),retained=prior.filter(item=>!affected.includes(item));if(ranked.some(m=>!used.has(String(m.id))))resolveRotatedMealSlots(plan,[current],retained);weekdayMealOverrides={...plan.weekdayMealOverrides};
 saveWeekdayMealOverrides();reconcileActiveLinkedMeals();reconcileRotatedGroceryChecks(grocery,affected.map(item=>({...item,planId:plan.id})));
 persist();finishSkippedCookingUndo(skipUndo);renderList();return true;
}

function hiddenLinkedSides(plan,day,category,parent){
 if(!day||!plan)return [];
 const entries=getDisplayedWeekdayMealsForPlan(plan),owner=entries.find(entry=>entry.day===day&&entry.cat===category&&String(entry.meal.id)===String(parent.id));if(!owner)return [];
 return [...new Set((parent.linkedMealIds||[]).map(String))].map(id=>meals.find(meal=>String(meal.id)===String(id))).filter(side=>{
  if(!side)return false;const cat=linkedRecipePlacement(plan,day,owner,side,entries),choice=plan.cycleSlotChoices?.[weekdaySlotKey(day,cat)],temp=weekSchedule(plan).slots[temporarySlotKey(day,cat)];
  const hidden=temp?.kind==='empty'||(choice?.blockedParents||[]).some(id=>String(id)===String(parent.id))||(choice?.excludedMealIds||[]).some(id=>String(id)===String(side.id));
  return hidden&&!entries.some(entry=>entry.day===day&&entry.cat===cat&&String(entry.meal.id)===String(side.id));
 }).map(side=>({side,cat:linkedRecipePlacement(plan,day,owner,side,entries)}));
}
function restoreHiddenLinkedSide(day,category,parent,sideId){
 const plan=mealPlans.find(p=>p.id===activePlanId),hidden=hiddenLinkedSides(plan,day,category,parent).find(item=>String(item.side.id)===String(sideId));if(!hidden)return false;
 const rememberedAmounts=heldWeekGroceryQuantities(plan),remembered={...heldWeekGroceryChecks(plan),...(weekSchedule(plan).linkedGroceryChecks||{})},side=hidden.side,cat=hidden.cat,otherHidden=hiddenLinkedSides(plan,day,category,parent).filter(item=>item.cat===cat&&String(item.side.id)!==String(side.id)).map(item=>String(item.side.id));
 const previous=readPreviousRotation(),cycled=previous?.cookingCycledContexts||[],oldPlan=previous?.mealPlans.find(item=>item.id===plan.id),sameParent=oldPlan&&getDisplayedWeekdayMealsForPlan(oldPlan,null,previous).some(entry=>entry.day===day&&entry.cat===category&&String(entry.meal.id)===String(parent.id));
 if(previous&&sameParent&&cycled.some(item=>item.planId===plan.id&&item.day===day&&item.cat===cat&&String(item.mealId)===String(side.id))&&!cycled.some(item=>item.planId===plan.id&&item.day===day&&String(item.mealId)===String(parent.id))){for(const [id,checked]of Object.entries(previous.groceryOccurrenceChecks?.checks||{}))if(!Object.hasOwn(remembered,id))remembered[id]=checked}
 previouslyActiveLinkedIds.add(String(side.id));
 const result=changeTemporaryWeek(current=>{
  clearTemporarySlot(current,day,cat);const key=weekdaySlotKey(day,cat),old=current.cycleSlotChoices?.[key]||{};
  current.cycleSlotChoices={...(current.cycleSlotChoices||{}),[key]:{...old,mealId:String(side.id),parentId:String(parent.id),retain:false,substitution:false,empty:false,blockedParents:(old.blockedParents||[]).filter(id=>String(id)!==String(parent.id)),excludedMealIds:[...new Set([...(old.excludedMealIds||[]).filter(id=>String(id)!==String(side.id)),...otherHidden])]}};
  if(rotationGroupScheduled(current,day,cat)){setWeekdayOverride(day,cat,side.id);current.weekdayMealOverrides={...weekdayMealOverrides};current.cycleRetainedSlots={...(current.cycleRetainedSlots||{}),[key]:String(side.id)}}
 });
 if(result){for(const source of getGroceryContributions(true))if(source.planId===plan.id&&source.day===day&&source.cat===cat&&String(source.mealId)===String(side.id)){const saved=remembered[source.id]??remembered[source.legacyId];if(typeof saved==='boolean')groceryOccurrenceChecks.checks[source.id]=saved;const amount=rememberedAmounts[source.id];if(amount)(groceryOccurrenceChecks.quantities??={})[source.id]={...amount}}saveGroceryOccurrenceChecks();saveActiveMealPlan();renderList()}
 return result;
}
function openTopMealActionMenu(day,category,meal,fromLinkedGroup=false,cookingOverride=null,navigationOrigin=null){
 const plan=mealPlans.find(p=>p.id===activePlanId);
 const select=()=>{const occasional=category==='@day'||!getDayCategories(day).length||String(plan?.occasionalMeals?.[day])===String(meal.id),current=occasional?getDisplayedWeekdayMeals().find(item=>item.day===day&&item.occasional&&!item.linkedTo)?.meal:meal;openWeekdayMealChooser(day,category==='@day'?null:category,current||meal,occasional)};
 if(meal.temporaryMeal){
  const dialog=compactMealDialog(meal.name,'One-time meal options');
  compactMealLinks(dialog,[['Select',select],['Edit',()=>openOneTimeMealEditor(day,category,meal)]]);
  compactMealButton(dialog,slotEmptyLabel(day,category),()=>leaveWeekEmpty(day,category));
  if(underlyingSlotMeal(plan,day,category))compactMealButton(dialog,'Resume planned meal',()=>resumeWeekSlot(day,category));
  for(const item of hiddenLinkedSides(plan,day,category,meal))compactMealButton(dialog,'Restore '+item.side.name,()=>restoreHiddenLinkedSide(day,category,meal,item.side.id));
  return;
 }
 navigationOrigin=navigationOrigin||captureMealEditorOrigin();
 const dialog=compactMealDialog(meal.name||'Meal options',day?'Meal options for '+day:'Meal options');
 dialog.box.querySelector('h3').classList.add('meal-options-recipe-title');dialog.box.querySelector('button').setAttribute('aria-label','Close meal options');
 const edit=()=>fromLinkedGroup?openLinkedMealEditorInline(meal,navigationOrigin):openEditor(meal.id,false,navigationOrigin);
 const links=[];if(day){links.push(['Select',select]);const entry=getDisplayedWeekdayMeals().find(item=>item.day===day&&item.cat===category&&String(item.meal.id)===String(meal.id));if(rotationGroupScheduled(plan,day,category)&&!entry?.occasional)links.push(['Skip',()=>skipScheduledMeal(day,category,meal)])}links.push(['Edit',edit]);
 compactMealLinks(dialog,links);
  const cooked=document.createElement('button');cooked.type='button';cooked.className='meal-options-last-cooked';cooked.style.cssText='display:flex;align-items:center;gap:6px;border:0;background:transparent;color:#707782;font:inherit;font-size:12px;font-weight:400;padding:2px 0;min-height:36px;max-width:100%;text-align:left;margin:0 0 12px';const cookedText=document.createElement('span');cooked.append(cookedText);cooked.insertAdjacentHTML('beforeend','<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+appIconSvg.rename+'</svg>');
  function refreshCooked(){const current=meals.find(record=>String(record.id)===String(meal.id)),label=lastCookedLabel(current||meal);cookedText.textContent=label?label.replace(/^Last cooked /,'Last cooked: '):'Last cooked: Never';cooked.title='Edit last cooked date';cooked.setAttribute('aria-label',cookedText.textContent+' — Edit date for '+(current?.name||meal.name||'recipe'))}
  cooked.onclick=e=>{e.preventDefault();e.stopPropagation();const current=meals.find(record=>String(record.id)===String(meal.id));if(current)editMealCookedDate(current,()=>{if(cooked.isConnected){refreshCooked();cooked.focus({preventScroll:true})}},cookingOverride||currentRecipeContext(day,category,current))};refreshCooked();

 dialog.box.append(cooked);
 {const favorite=recipeFavoriteButton(meal);favorite.classList.add('meal-options-favorite');dialog.box.firstElementChild.insertBefore(favorite,dialog.box.firstElementChild.lastElementChild)}
 compactMealButton(dialog,'Open recipe',()=>openSavedMealRecipe(meal,cookingOverride||currentRecipeContext(day,category,meal),navigationOrigin));
 if(!day)compactMealButton(dialog,'Schedule Meal',()=>openScheduleMealDialog(meal));
 if(day)compactMealButton(dialog,slotEmptyLabel(day,category),()=>leaveWeekEmpty(day,category));
 compactMealButton(dialog,'Edit grocery list',()=>openTopIngredientChooser(meal));
 for(const item of hiddenLinkedSides(plan,day,category,meal))compactMealButton(dialog,'Restore '+item.side.name,()=>restoreHiddenLinkedSide(day,category,meal,item.side.id));
}
function confirmDuplicateMealChoice(meal,occurrences,target=null){return new Promise(resolve=>{
 const shade=document.createElement('div');shade.style.cssText='position:fixed;inset:0;z-index:20000;background:#0008;display:flex;align-items:center;justify-content:center;padding:18px';
 const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label',(meal.name||'Meal')+' is already planned');panel.style.cssText='background:#fff;color:#242424;border-radius:14px;padding:18px;width:min(440px,100%);max-height:80vh;overflow-y:auto';
 function finish(value){shade.remove();resolve(value)}
 const header=document.createElement('div');header.style.cssText='display:flex;align-items:center;gap:10px;margin-bottom:12px';
 const title=document.createElement('h3');title.textContent=(meal.name||'Meal')+' is already planned';title.style.cssText='margin:0;flex:1;min-width:0;overflow-wrap:anywhere';
 const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close');close.onclick=()=>finish(null);header.append(title,close);panel.append(header);
 let selected=occurrences.length===1?occurrences[0]:null;
 const message=document.createElement('p');message.style.cssText='margin:0 0 14px';panel.append(message);
 const yes=document.createElement('button');yes.type='button';yes.className='smallbtn';yes.style.cssText='display:block;width:100%;min-height:44px;padding:12px;text-align:left;white-space:normal;margin-bottom:10px';
 function update(){const sameDay=selected&&target?.day===selected.day;
  message.textContent=selected?sameDay?(meal.name||'Meal')+' is scheduled for '+selected.day+' · '+selected.cat+'. Would you like to move it to '+target.category+'?':(meal.name||'Meal')+' is scheduled for '+selected.day+". Would you like to replace "+selected.day+"'s meal?":(meal.name||'Meal')+(target&&occurrences.some(item=>item.day===target.day)?' is scheduled on multiple weekdays or groups. Choose which occurrence to replace.':' is scheduled on multiple weekdays. Choose which occurrence to replace.');
  yes.textContent=selected?sameDay?'Yes — Move meal':'Yes — Replace '+selected.day+"'s meal":'Yes — Replace selected meal';yes.disabled=!selected;
 }
 if(occurrences.length>1){const select=document.createElement('select');select.setAttribute('aria-label','Occurrence to replace');select.style.cssText='width:100%;min-height:44px;padding:8px;margin-bottom:14px;border:1px solid #ccc;border-radius:8px;background:#fff';const blank=document.createElement('option');blank.value='';blank.textContent='Choose an occurrence';select.append(blank);occurrences.forEach((item,index)=>{const option=document.createElement('option');option.value=String(index);option.textContent=item.day+' · '+item.cat;select.append(option)});select.onchange=()=>{selected=select.value===''?null:occurrences[Number(select.value)];update()};panel.append(select)}
 yes.onclick=()=>finish({replace:selected});const no=document.createElement('button');no.type='button';no.className='smallbtn';no.textContent='No — Keep both meals';no.style.cssText='display:block;width:100%;min-height:44px;padding:12px;text-align:left;white-space:normal';no.onclick=()=>finish({replace:null});update();panel.append(yes,no);shade.append(panel);shade.onclick=e=>{if(e.target===shade)finish(null)};shade.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();finish(null)}};document.body.append(shade);close.focus({preventScroll:true});
})}
function applyManualWeekdayMeal(day,category,meal,replacing=null,occasional=false,options={}){
 if(!options.startGroup&&(category==='@day'||!getDayCategories(day).length)){category=null;occasional=true}
 const groceryBefore=captureGroceryCheckStates(),beforeIds=new Set(getDisplayedWeekdayMeals().map(({meal})=>String(meal.id)));
 saveActiveMealPlan();const beforeState=options.beforeState||JSON.parse(captureState()),plan=mealPlans.find(plan=>plan.id===activePlanId);
 const sameDayMove=replacing&&replacing.day===day&&replacing.cat!==category;
 if(options.schedulingOnly||sameDayMove||weekSchedule(plan).slots[temporarySlotKey(day,category)]){beforeState.scheduleChangeUndo={sourceIds:[],checks:Object.fromEntries([...groceryBefore].map(([id,item])=>[id,item.checked])),restoreOrder:!!replacing};beforeState.skippedCookingState=captureSkippedCookingState(plan,{day,cat:category,meal:{id:'schedule-change'}});if(replacing){const other=captureSkippedCookingState(plan,replacing),saved=beforeState.skippedCookingState;saved.keys.push(...other.keys);Object.assign(saved.sessions,other.sessions);Object.assign(saved.scales,other.scales)}}
 clearTemporarySlot(plan,day,category);
 const prior=getDisplayedWeekdayMealsForPlan(plan),moving=replacing?cycleAffectedEntries(prior.map(item=>({...item,planId:plan.id})),[{...replacing,planId:plan.id}],plan):[];
 const rotateSource=replacing&&!sameDayMove&&rotationGroupScheduled(plan,replacing.day,replacing.cat);
 if(rotateSource&&beforeState.scheduleChangeUndo){const occurrences=new Set(moving.map(item=>groceryOccurrenceIdentity(plan,item)));beforeState.scheduleChangeUndo.sourceIds=[...groceryBefore].filter(([,item])=>occurrences.has(item.source.occurrence)).map(([id])=>id)}
 if(!rotateSource&&!options.quiet)snapshot(JSON.stringify(beforeState));preserveOtherMealPlanChoices(day,category);
 if(options.startGroup){
  weekdayCategories[day]=[category];
  if(String(plan.occasionalMeals?.[day])===String(meal.id))delete plan.occasionalMeals[day];
 }
 if(occasional){
  const slot=prior.find(item=>item.day===day&&item.occasional&&!item.linkedTo&&rotationGroupScheduled(plan,day,item.cat));
  plan.occasionalMeals={...(plan.occasionalMeals||{}),[day]:String(meal.id)};
  if(slot){const key=weekdaySlotKey(day,slot.cat);setWeekdayOverride(day,slot.cat,meal.id);plan.cycleRetainedSlots[key]=String(meal.id);plan.cycleSlotChoices[key]={mealId:String(meal.id),parentId:'',retain:true,substitution:true,occasional:true,...(options.schedulingOnly?{preserveSideQueue:true}:{}),blockedParents:[]}}
 }else{
  const key=weekdaySlotKey(day,category),oldChoice=plan.cycleSlotChoices?.[key],displaced=prior.find(item=>item.day===day&&item.cat===category);
  const deferredMealIds=[...new Set([...(oldChoice?.deferredMealIds||[]),...(displaced&&!manualWeekdayMealChoice(plan,day,category,displaced.meal.id)?[String(displaced.meal.id)]:[])])];setWeekdayOverride(day,category,meal.id);
  plan.cycleRetainedSlots={...(plan.cycleRetainedSlots||{}),[key]:String(meal.id)};
  plan.cycleSlotChoices={...(plan.cycleSlotChoices||{}),[key]:options.automatic?{...(oldChoice||{}),mealId:String(meal.id),parentId:'',empty:false,retain:false,substitution:false,blockedParents:[]}:{mealId:String(meal.id),parentId:'',retain:true,substitution:true,deferredMealIds,...(options.schedulingOnly?{preserveSideQueue:true}:{}),blockedParents:[]}};
 }
 if(sameDayMove)editableWeekSchedule(plan).slots[temporarySlotKey(replacing.day,replacing.cat)]={kind:'empty'};
 if(replacing?.occasional)delete plan.occasionalMeals[replacing.day];
 saveWeekdayMealOverrides();
 // Materialize retained checks and explicitly uncheck all newly added quantities.
 reconcileRotatedGroceryChecks(groceryBefore,[]);
 if(replacing){
  const from=new Set(moving.map(item=>groceryOccurrenceIdentity(plan,item))),transfers=new Map();
  for(const {source,checked} of groceryBefore.values())if(from.has(source.occurrence)){const token=JSON.parse(source.id);transfers.set(JSON.stringify([String(source.mealId),token[1],token[2]]),checked)}
  const target=getDisplayedWeekdayMealsForPlan(plan).find(item=>item.day===day&&(occasional?item.occasional:item.cat===category)&&String(item.meal.id)===String(meal.id));
  const destination=new Set(target?cycleAffectedEntries(getDisplayedWeekdayMealsForPlan(plan).map(item=>({...item,planId:plan.id})),[{...target,planId:plan.id}],plan).map(item=>groceryOccurrenceIdentity(plan,item)):[]);
  for(const source of getGroceryContributions(true))if(destination.has(source.occurrence)&&!groceryBefore.has(source.id)){const token=JSON.parse(source.id),checked=transfers.get(JSON.stringify([String(source.mealId),token[1],token[2]]));if(typeof checked==='boolean')groceryOccurrenceChecks.checks[source.id]=checked}
  saveGroceryOccurrenceChecks();
  if(rotateSource)moveDisplayedMealsToBottom(new Set([weekdaySlotKey(replacing.day,replacing.cat)]),false,false,null,beforeState);
  else{resetGroceriesForNewTopMeals(beforeIds);persist();if(!options.quiet)renderList()}
 }else{resetGroceriesForNewTopMeals(beforeIds);persist();if(!options.quiet)renderList()}
 if(!options.quiet)finishScheduleChangeUndo(beforeState);return beforeState;
}

function openWeekdayMealChooser(day,category,currentMeal,occasional=false){
 const assigned=getDayCategories(day),order=[...assigned,...masterOrderedGroups(masterDisplayOrder()).filter(cat=>!assigned.includes(cat))];
 const expanded=new Set(assigned);let pendingMeal=currentMeal,highlights;
 const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:10001;display:flex;align-items:center;justify-content:center;padding:16px';
 const box=document.createElement('div');box.className='weekday-meal-picker';box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label','Choose '+day+"'s meal");box.style.cssText='background:white;color:#222;border-radius:14px;padding:18px;max-width:520px;width:100%;max-height:80vh;overflow:hidden;display:flex;flex-direction:column;gap:10px;box-shadow:0 8px 30px #0004';
 const header=document.createElement('div');header.style.cssText='display:flex;align-items:center;gap:8px;flex-shrink:0';
 const title=document.createElement('h3');title.textContent='Choose '+day+"'s "+(assigned.length>1?category+' ':'')+'meal';title.style.cssText='margin:0;min-width:0;flex:1;overflow-wrap:anywhere';
 const searchButton=document.createElement('button');searchButton.type='button';searchButton.setAttribute('aria-label','Search recipes');searchButton.title='Search recipes';searchButton.setAttribute('aria-expanded','false');searchButton.style.cssText='border:0;background:transparent;display:grid;place-items:center;flex:0 0 44px;width:44px;height:44px;color:#444';searchButton.innerHTML='<svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="7"/><path d="m16 16 5 5"/></svg>';header.append(title,searchButton);
 const search=document.createElement('input');search.type='search';search.hidden=true;search.placeholder='Search recipes';search.setAttribute('aria-label','Search recipes');search.style.cssText='width:100%;min-height:44px;flex-shrink:0;padding:9px;border:1px solid #ccc;border-radius:8px;background:white';
 const list=document.createElement('div');list.className='weekday-meal-picker-list';list.style.cssText='overflow-y:auto;min-height:0;flex:1;overscroll-behavior:contain';
 function recipeButton(meal,showGroup=false){
  const flagged=meal.needsTweaking===true,button=document.createElement(flagged?'div':'button');if(!flagged)button.type='button';else{button.setAttribute('role','group');button.setAttribute('aria-label',meal.name||'Recipe')}button.className='weekday-meal-choice';button.dataset.mealId=String(meal.id);const selected=String(meal.id)===String(pendingMeal?.id);if(!flagged)button.setAttribute('aria-pressed',String(selected));
  button.style.cssText='display:block;width:100%;min-height:45px;text-align:left;padding:5px 8px;margin:0;border:0;border-radius:8px;background:'+(highlights.featuredColorById.get(String(meal.id))||'white')+';color:#222;font-size:16px;overflow-wrap:anywhere';
  if(highlights.featuredColorById.has(String(meal.id)))button.style.paddingLeft='13px';
  const name=document.createElement('span'),fullName=meal.name||'Untitled meal';name.textContent=fullName;
  if(flagged){const space=fullName.lastIndexOf(' '),ending=document.createElement('span');ending.className='recipe-tweaking-name-ending';const select=document.createElement('button');select.type='button';select.className='weekday-meal-choice-name';select.textContent=space>0?fullName.slice(space+1):fullName;select.setAttribute('aria-label',fullName);select.setAttribute('aria-pressed',String(selected));name.textContent=space>0?fullName.slice(0,space)+' ':'';ending.append(select);appendNeedsTweakingIndicator(ending,meal,renderChoices);button.append(name,ending)}else button.append(name);
  
  if(showGroup){const group=document.createElement('small');group.textContent=meal.cat;group.style.cssText='display:block;color:#666;font-size:12px;margin-top:3px';button.append(group)}
  const cooked=lastCookedLabel(meal);if(cooked){const info=document.createElement('span');info.className='weekday-choice-cooked';info.textContent=cooked;info.style.cssText='display:block;font-size:12px;color:#69717a;margin-top:3px';button.append(info)}
  appendScheduledRecipeWeekdays(button,meal,highlights.scheduledDaysByMeal);
  button.onclick=()=>{pendingMeal=meal;renderChoices()};return button;
 }
 function renderChoices(){
  const scroll=list.scrollTop;highlights=scheduledRecipeHighlights(pendingMeal&&String(pendingMeal.id)!==String(currentMeal?.id)?{day,category,meal:pendingMeal,occasional}:null);list.replaceChildren();
  if(normalizeSearchText(search.value)){
   const matches=order.flatMap(cat=>masterRecipeOrder(cat).filter(meal=>mealMatchesSearch(meal,search.value)));
   for(const meal of matches)list.append(recipeButton(meal,true));
   if(!matches.length){const empty=document.createElement('p');empty.textContent='No matching meals.';empty.style.color='#666';list.append(empty)}
  }else for(const cat of order){
   const entries=masterRecipeOrder(cat),open=expanded.has(cat);
   const card=document.createElement('div');card.className='master-category-card';card.dataset.group=cat;card.style.marginBottom='6px';
   const toggle=document.createElement('button');toggle.type='button';toggle.className='master-category-title';toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-label',cat+' ('+entries.length+' recipes)');toggle.style.cssText='width:100%;min-height:44px;padding:10px;gap:8px';
   const arrow=document.createElementNS('http://www.w3.org/2000/svg','svg');arrow.setAttribute('viewBox','0 0 24 24');arrow.setAttribute('aria-hidden','true');arrow.innerHTML='<path d="'+(open?'m6 15 6-6 6 6':'m6 9 6 6 6-6')+'"/>';
   const name=document.createElement('strong');name.textContent=cat;name.style.flex='1';const count=document.createElement('span');count.className='master-category-count';count.textContent=entries.length+' '+(entries.length===1?'recipe':'recipes');toggle.append(arrow,name,count);
   toggle.onclick=()=>{if(expanded.has(cat))expanded.delete(cat);else expanded.add(cat);renderChoices()};card.append(toggle);
   if(open){const body=document.createElement('div');body.className='master-category-meals';for(const meal of entries)body.append(recipeButton(meal));if(!entries.length){const empty=document.createElement('p');empty.textContent='No recipes in this group.';empty.className='muted';body.append(empty)}card.append(body)}list.append(card);
  }
  list.scrollTop=scroll;
 }
 search.oninput=()=>{list.scrollTop=0;renderChoices()};searchButton.onclick=()=>{search.hidden=!search.hidden;searchButton.setAttribute('aria-expanded',String(!search.hidden));if(search.hidden){search.value='';renderChoices();searchButton.focus()}else search.focus()};
 const scheduleObserver=new MutationObserver(()=>{if(overlay.isConnected)renderChoices()});
 const scheduleList=document.getElementById('list');if(scheduleList)scheduleObserver.observe(scheduleList,{childList:true});
 const actions=document.createElement('div');actions.className='meal-unified-actions';actions.style.flexShrink='0';
 function close(){scheduleObserver.disconnect();window.visualViewport?.removeEventListener('resize',fit);window.visualViewport?.removeEventListener('scroll',fit);overlay.remove()}
 function fit(){const view=window.visualViewport;if(!view)return;overlay.style.top=view.offsetTop+'px';overlay.style.bottom='auto';overlay.style.height=view.height+'px';box.style.maxHeight=Math.min(innerHeight*.8,Math.max(120,view.height-32))+'px'}
 const save=document.createElement('button');save.type='button';setIconButton(save,'save','Save');save.onclick=async()=>{
  if(!pendingMeal||String(pendingMeal.id)===String(currentMeal?.id)){close();return}
  if(groceryCheckStorageInvalid){showAppMessage('Saved grocery check states could not be read. Export a backup before repairing this browser data.');return}
  save.disabled=true;const planId=activePlanId,selectedMeal=pendingMeal;
  try{
   const plan=mealPlans.find(plan=>plan.id===planId),duplicates=getDisplayedWeekdayMeals().filter(item=>!(item.day===day&&item.cat===category)&&String(item.meal.id)===String(selectedMeal.id)&&(rotationSelectable(item,plan)||item.occasional&&!item.linkedTo));
   const decision=duplicates.length?await confirmDuplicateMealChoice(selectedMeal,duplicates,{day,category}):{replace:null};
   if(!overlay.isConnected||activePlanId!==planId)return;
   if(!decision){pendingMeal=currentMeal;renderChoices();return}
   applyManualWeekdayMeal(day,category,selectedMeal,decision.replace,occasional);close();
  }finally{save.disabled=false}
 };
 const create=document.createElement('button');create.type='button';setIconButton(create,'add','Create New Meal');create.style.cssText+=';flex:0 0 44px;width:44px;height:44px';create.onclick=()=>{const target={planId:activePlanId,day,category,occasional};overlay.style.display='none';const opened=openCreateScheduledRecipe(target,{complete:close,cancel:()=>{overlay.style.display='flex';create.focus({preventScroll:true})}});if(!opened)overlay.style.display='flex'};header.append(create);
 const cancel=document.createElement('button');cancel.type='button';setIconButton(cancel,'cancel','Cancel');cancel.onclick=close;actions.append(save);if(occasional&&currentMeal){const remove=document.createElement('button');remove.type='button';setIconButton(remove,'delete','Remove scheduled meal');remove.onclick=async()=>{if(await appDialog('Remove '+(currentMeal.name||'this meal')+' from '+day+'?',null,'yesno',[],'This removes only the scheduled meal from '+day+'. Saved recipes and permanent group assignments will not be deleted.')){removeOccasionalMeal(day);close()}};actions.append(remove)}actions.append(cancel);box.append(header,search,list,actions);overlay.append(box);
 overlay.addEventListener('click',event=>{if(event.target===overlay)close()});overlay.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();close()}});document.body.append(overlay);window.visualViewport?.addEventListener('resize',fit);window.visualViewport?.addEventListener('scroll',fit);fit();renderChoices();
}

// The expanded Top Recipes list edits the same saved ingredient records as the
// grocery chooser. Keep its selection and grocery check status when renaming.
async function editTopRecipeIngredient(meal,originalLine){
  const response=await editGroceryIngredientDialog(originalLine);
  if(!response||response.action==='cancel')return;
  if(!Array.isArray(meal.ingredients))return;
  const index=meal.ingredients.findIndex(x=>String(x).trim()===originalLine);
  if(index<0)return;
  let newLine='';
  if(response.action==='delete'){
    if(!await appDialog('Delete ingredient “'+originalLine+'”?',null,'yesno'))return;
  }else if(response.action==='save'){
    newLine=String(response.value||'').trim();
    if(!newLine){await showAppMessage('Enter an ingredient name.');return}
    if(newLine===originalLine)return;
    if(meal.ingredients.some((x,i)=>i!==index&&String(x).trim().toLowerCase()===newLine.toLowerCase())){
      await showAppMessage('That ingredient is already in this list.');return;
    }
  }else return;
  snapshot();preserveGroceryCheckStates(captureGroceryCheckStates());
  const selectionKey=String(meal.id);
  let chosen={};
  try{chosen=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}')}catch(e){}
  if(!chosen||typeof chosen!=='object'||Array.isArray(chosen))chosen={};
  const originalChoices=Array.isArray(chosen[selectionKey])?chosen[selectionKey]:meal.groceryDefaultAll===true?[...meal.ingredients]:[];
  if(response.action==='delete'){
    meal.ingredients.splice(index,1);
    chosen[selectionKey]=originalChoices.filter(x=>x!==originalLine);
  }else{
    meal.ingredients[index]=newLine;
    chosen[selectionKey]=originalChoices.map(x=>x===originalLine?newLine:x);
    const oldKey=originalLine.toLowerCase().replace(/\s+/g,' ').trim();
    const newKey=newLine.toLowerCase().replace(/\s+/g,' ').trim();
    if(checkedIngredients.has(oldKey))checkedIngredients.add(newKey);
  }
  try{
    localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(chosen));
    localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));
  }catch(e){}
  if(newLine)renameGrocerySourceChecks(meal,originalLine,newLine);saveGroceryOccurrenceChecks();
  persist();
  renderList();
}
function editGroceryIngredientDialog(initial){return new Promise(resolve=>{
  const shade=document.createElement('div');shade.style.cssText='position:fixed;inset:0;z-index:13050;background:#0008;display:flex;align-items:center;justify-content:center;padding:18px';
  const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Edit ingredient');panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:22px;width:100%;max-width:480px;box-shadow:0 12px 36px #0003';
  const heading=document.createElement('div');heading.textContent='Edit ingredient';heading.style.cssText='font-size:19px;font-weight:600;margin-bottom:18px';
  const field=document.createElement('input');field.type='text';field.value=initial;field.setAttribute('aria-label','Ingredient');field.style.cssText='width:100%;border:1px solid #ccc;border-radius:9px;padding:12px;margin-bottom:20px;background:#fff;color:#242424;font:inherit';
  const actions=document.createElement('div');actions.style.cssText='display:flex;align-items:center;justify-content:space-evenly;gap:12px';
  let frame=0;
  function fit(){if(!shade.isConnected)return;cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{if(!shade.isConnected)return;const vv=window.visualViewport;const top=vv?vv.offsetTop:0;const height=vv?vv.height:window.innerHeight;shade.style.top=top+'px';shade.style.bottom='auto';shade.style.height=height+'px';shade.style.overflowY='auto';panel.style.maxHeight=Math.max(160,height-24)+'px';panel.style.overflowY='auto'})}
  function finish(action){window.visualViewport?.removeEventListener('resize',fit);window.visualViewport?.removeEventListener('scroll',fit);document.removeEventListener('keydown',keyHandler);cancelAnimationFrame(frame);shade.remove();resolve({action,value:field.value})}
  const save=document.createElement('button');save.type='button';setIconButton(save,'save','Save ingredient');save.onclick=()=>finish('save');
  const remove=document.createElement('button');remove.type='button';setIconButton(remove,'delete','Delete ingredient');remove.onclick=()=>finish('delete');
  const cancel=document.createElement('button');cancel.type='button';setIconButton(cancel,'cancel','Cancel');cancel.onclick=()=>finish('cancel');
  for(const btn of [save,remove,cancel]){btn.style.minWidth='52px';btn.style.minHeight='48px'}
  const keyHandler=e=>{if(e.key==='Escape'){e.preventDefault();finish('cancel')}else if(e.key==='Enter'){e.preventDefault();finish('save')}};
  actions.append(save,remove,cancel);panel.append(heading,field,actions);shade.append(panel);document.body.append(shade);
  window.visualViewport?.addEventListener('resize',fit);window.visualViewport?.addEventListener('scroll',fit);document.addEventListener('keydown',keyHandler);
  fit();field.focus({preventScroll:true});field.select();requestAnimationFrame(fit)
})}

function mealLinkedCopies(meal){
 if(!meal)return[];
 return meals.filter(m=>String(m.id)===String(meal.id)||
  (meal.linkGroup&&m.linkGroup===meal.linkGroup)||
  (meal.importSourceId&&m.importSourceId===meal.importSourceId));
}
function grocerySelectionsForMeal(meal,selections){
 if(meal.temporaryMeal)return meal.ingredients||[];
 const merged=new Map(),copies=mealLinkedCopies(meal),explicit=copies.some(copy=>Array.isArray(selections?.[String(copy.id)]));
 // An explicit choice (including an empty list) wins over defaults on new memberships.
 for(const copy of copies){
  const saved=selections&&selections[String(copy.id)],entries=Array.isArray(saved)?saved:!explicit&&copy.groceryDefaultAll===true?copy.ingredients:[];
  if(Array.isArray(entries))for(const entry of entries){const line=String(entry).trim();if(line)merged.set(ingredientKey(line),line)}
 }
 return [...merged.values()];
}
function openTopIngredientChooser(meal){
 if(meal.temporaryMeal){const entry=getDisplayedWeekdayMeals().find(item=>String(item.meal.id)===String(meal.id));if(entry)openOneTimeMealEditor(entry.day,entry.cat,meal);return}
  meal={...meal,ingredients:Array.isArray(meal.ingredients)?[...meal.ingredients]:[]};
  const groceryBefore=captureGroceryCheckStates();
  let selectedByMeal={};try{selectedByMeal=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}')}catch(e){}
  const key=String(meal.id);selectedByMeal[key]=grocerySelectionsForMeal(meal,selectedByMeal);
  const originalRecipeRecord=JSON.parse(JSON.stringify(meal));if(!Array.isArray(meal.ingredients))meal.ingredients=[];const originalIngredients=[...meal.ingredients];const originalSelected=[...selectedByMeal[key]];
  let pendingRecipeUrl=String(meal.url||'');
  let pendingIngredientImportUrl=String(meal.ingredientImportUrl||'');let pendingRecipeDetails=null;
  const overlay=document.createElement('div');overlay.dataset.recipeEditDraft='true';overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:10000;display:flex;align-items:center;justify-content:center;padding:16px';
  const box=document.createElement('div');box.style.cssText='background:white;color:#222;border-radius:14px;padding:18px;max-width:520px;width:100%;max-height:80vh;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 8px 30px #0004';
  const title=document.createElement('h3');title.textContent='Add ingredients to grocery list';title.style.marginTop='0';
  const list=document.createElement('div');list.style.cssText='overflow-y:auto;min-height:0;flex:1 1 auto';
  const checks=[];const manualReselections=new Set();
  const renamedIngredients=[];
  overlay.mealRecoveryDraft={ownerId:'grocery:'+key,kind:'ingredient-editor',capture:()=>({recipe:JSON.parse(JSON.stringify(meal)),selectedIngredients:checks.filter(x=>x.cb.checked).map(x=>x.line),pendingRecipeUrl,pendingIngredientImportUrl,pendingRecipeDetails,renamedIngredients:[...renamedIngredients]}),dirty:()=>true,discard:()=>overlay.remove()};
  // Keep checkbox changes made in this dialog when a row has to be rebuilt.
  function rememberCheckedIngredients(){selectedByMeal[key]=checks.filter(x=>x.cb.checked).map(x=>x.line)}
  async function editGroceryIngredient(index,line){
    const choice=await editGroceryIngredientDialog(line);
    if(!overlay.isConnected||choice.action==='cancel')return;
    // Preserve all edits as pending until the grocery popup's main Save is pressed.
    if(choice.action==='delete'){
      if(!await appDialog('Delete ingredient “'+line+'”?',null,'yesno')||!overlay.isConnected)return;
      rememberCheckedIngredients();
      meal.ingredients.splice(index,1);
      selectedByMeal[key]=selectedByMeal[key].filter(x=>x!==line);
      renderIngredientRows();
      return;
    }
    const revised=String(choice.value).trim();
    if(!revised){await showAppMessage('Enter an ingredient name.');return}
    if(revised===line)return;
    if(meal.ingredients.some((item,i)=>i!==index&&String(item).trim().toLowerCase()===revised.toLowerCase())){
      await showAppMessage('That ingredient is already in this list.');return;
    }
    rememberCheckedIngredients();
    meal.ingredients[index]=revised;
    selectedByMeal[key]=selectedByMeal[key].map(item=>item===line?revised:item);
    renamedIngredients.push({from:line,to:revised});
    renderIngredientRows();
  }
  function renderIngredientRows(){
    list.innerHTML='';checks.length=0;
    meal.ingredients=(Array.isArray(meal.ingredients)?meal.ingredients:[]).map(x=>String(x).trim()).filter(Boolean);
    const orderedIngredients=meal.ingredients.map((line,index)=>({line,index}));
    orderedIngredients.sort((a,b)=>Number(selectedByMeal[key].some(item=>ingredientKey(item)===ingredientKey(b.line)))-Number(selectedByMeal[key].some(item=>ingredientKey(item)===ingredientKey(a.line))));
    orderedIngredients.forEach(({line,index})=>{
      const label=document.createElement('label');
      label.style.cssText='display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid #eee;touch-action:pan-y';
      label.title='Long press to edit ingredient; swipe right to delete';
      const cb=document.createElement('input');cb.type='checkbox';cb.checked=selectedByMeal[key].some(item=>ingredientKey(item)===ingredientKey(line));cb.style.cssText='flex:0 0 auto;margin-top:4px';cb.onchange=()=>{if(cb.checked)manualReselections.add(ingredientKey(line));rememberCheckedIngredients();const scroll=list.scrollTop;renderIngredientRows();list.scrollTop=scroll};
      const text=document.createElement('span');text.textContent=line;
      label.append(cb,text);
      let sx=0,sy=0,tracking=false,held=false,holdTimer=null;
      const cancelHold=()=>{clearTimeout(holdTimer);holdTimer=null};
      label.addEventListener('pointerdown',e=>{
        if(e.target===cb||(e.pointerType==='mouse'&&e.button!==0))return;
        sx=e.clientX;sy=e.clientY;tracking=true;held=false;
        cancelHold();
        holdTimer=setTimeout(()=>{if(!tracking)return;held=true;tracking=false;editGroceryIngredient(index,line)},550);
      },{passive:true});
      label.addEventListener('pointermove',e=>{
        if(tracking&&(Math.abs(e.clientX-sx)>12||Math.abs(e.clientY-sy)>12))cancelHold();
      },{passive:true});
      label.addEventListener('pointerup',e=>{
        cancelHold();
        if(held||!tracking){tracking=false;return}
        tracking=false;
        const dx=e.clientX-sx,dy=e.clientY-sy;
        if(dx>70&&dx>Math.abs(dy)*1.25){
          e.preventDefault();e.stopPropagation();
          if(confirm('Delete ingredient “'+line+'”?')){
            rememberCheckedIngredients();
            meal.ingredients.splice(index,1);
            selectedByMeal[key]=selectedByMeal[key].filter(x=>x!==line);
            renderIngredientRows();
          }
        }
      },{passive:false});
      ['pointerleave','pointercancel'].forEach(type=>label.addEventListener(type,()=>{cancelHold();tracking=false}));
      label.addEventListener('click',e=>{if(held){e.preventDefault();e.stopImmediatePropagation();held=false}},true);
      // Android may dispatch a delayed contextmenu for the *meal's* original
      // long press after this dialog opens. Never treat a contextmenu alone as
      // permission to edit a newly-created ingredient row. The row's own
      // pointerdown + hold timer above remains the editing gesture.
      label.addEventListener('contextmenu',e=>{
        e.preventDefault();cancelHold();tracking=false;
      });
      list.append(label);checks.push({line,cb});
    });
  }
  renderIngredientRows();
  const addRow=document.createElement('div');addRow.style.cssText='display:flex;gap:8px;align-items:center;padding-top:12px';
  const input=document.createElement('input');input.type='text';input.placeholder='Add an ingredient';input.setAttribute('aria-label','New recipe ingredient');input.style.cssText='min-width:0;flex:1;padding:10px;border:1px solid #bbb;border-radius:8px;font:inherit';
  const addBtn=document.createElement('button');addBtn.type='button';addBtn.className='smallbtn';addBtn.textContent='Add';
  function addIngredient(){const value=input.value.trim();if(!value)return;const exists=meal.ingredients.some(x=>String(x).trim().toLowerCase()===value.toLowerCase());if(exists){input.value='';return}rememberCheckedIngredients();meal.ingredients.push(value);selectedByMeal[key].push(value);renderIngredientRows();input.value='';input.focus()}
  addBtn.onclick=addIngredient;input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();addIngredient()}});addRow.append(input,addBtn);
  // The grocery chooser can import exactly like the meal editor, without
  // committing imported ingredients or URLs until its own Save is tapped.
  function mergeGroceryImport(lines){
    rememberCheckedIngredients();
    const existing=new Map((meal.ingredients||[]).map(line=>[String(line).trim().toLowerCase(),String(line).trim()]));
    for(const raw of lines){
      const line=cleanImportedIngredientDescriptors(raw);
      if(!line)continue;
      const normalized=line.toLowerCase();
      if(!existing.has(normalized)){
        meal.ingredients.push(line);
        existing.set(normalized,line);
      }
      const chosen=existing.get(normalized);
      if(!selectedByMeal[key].includes(chosen))selectedByMeal[key].push(chosen);
    }
    renderIngredientRows();
  }
  async function importGroceryFromLink(){
    const recipeUrl=pendingRecipeUrl.trim();
    let url=null,choice='other';
    if(recipeUrl){
      choice=await selectIngredientImportSource(true);
      if(!choice||!overlay.isConnected)return;
      url=choice==='recipe'?recipeUrl:await requestIngredientSourceUrl(pendingIngredientImportUrl,true);
    }else{
      url=await requestIngredientSourceUrl(pendingIngredientImportUrl,false);
      if(!url||!overlay.isConnected)return;
      const useAsRecipe=await askUseIngredientLinkAsRecipe();
      if(!overlay.isConnected)return;
      if(useAsRecipe)pendingRecipeUrl=url;
    }
    if(!url||!overlay.isConnected)return;
    const progress=showImportProgressDialog();
    try{
      const result=await Promise.race([
        importIngredientsFromWebsite(url,progress.signal).then(lines=>({lines})),
        progress.cancelled
      ]);
      if(!result.cancelled&&overlay.isConnected){
        mergeGroceryImport(result.lines);pendingRecipeDetails=result.lines.recipeDetails;
        if(choice==='other')pendingIngredientImportUrl=url;
        else pendingIngredientImportUrl='';
      }
    }catch(e){
      if(!progress.signal.aborted&&overlay.isConnected)showAppMessage(e.message||'Ingredients could not be imported.');
    }finally{progress.close()}
  }
  async function importGroceryFromPhoto(file){
    if(!file||!file.type.startsWith('image/')||!overlay.isConnected)return;
    const progress=showImportProgressDialog('Reading ingredients from photo…');
    let deadline=null;
    try{
      const timedOut=new Promise(resolve=>{deadline=setTimeout(()=>resolve({timedOut:true}),60000)});
      const result=await Promise.race([
        (async()=>{
          if(await ingredientPhotoIsBlank(file))return {blank:true};
          if(progress.signal.aborted)return {cancelled:true};
          return {text:await recognizeIngredientPhoto(file,progress.signal)};
        })(),
        progress.cancelled,
        timedOut
      ]);
      if(result.timedOut)progress.abort();
      progress.close();
      if(result.cancelled||!overlay.isConnected)return;
      if(result.timedOut){await showAppMessage('The photo could not be read in time. Try a closer photo of the ingredients or enter them manually.');return}
      if(result.blank){await showAppMessage('No readable ingredients found in that photo. Try a photo containing an ingredient list.');return}
      const originalText=String(result.text||'').trim();
      if(!originalText){await showAppMessage('No readable text was found in the photo. Try a clearer picture or enter ingredients manually.');return}
      const extracted=extractPhotoIngredientLines(originalText);
      if(!extracted.lines.length){await showAppMessage('No clear ingredient list was found. Try a close-up photo of just the ingredients, or enter them manually.');return}
      const reviewed=await reviewPhotoIngredients(extracted.lines.join('\n'),originalText);
      if(reviewed!==null&&overlay.isConnected){mergeGroceryImport(reviewed.split(/\r?\n/));const sections=recipeTextSections(originalText);if(sections.instructions.length||sections.notes)pendingRecipeDetails={...(pendingRecipeDetails||{}),...sections};}
    }catch(e){
      progress.close();
      if(!progress.signal.aborted&&overlay.isConnected)await showAppMessage('Photo ingredients could not be read. Check your connection or enter them manually.');
    }finally{
      if(deadline!==null)clearTimeout(deadline);
      progress.close();
    }
  }
  const importRow=document.createElement('div');
  importRow.style.cssText='display:flex;flex-direction:column;align-items:flex-start;gap:8px;margin-top:12px;width:100%;flex:0 0 auto';
  const importLabel=document.createElement('span');importLabel.textContent='Import ingredients';importLabel.style.cssText='font-size:14px;color:#666';
  const importButtons=document.createElement('div');
  importButtons.style.cssText='display:flex;align-items:center;justify-content:flex-start;gap:10px;flex-wrap:wrap;width:100%';
  importRow.append(importLabel,importButtons);
  function importIcon(label,path,callback){
    const btn=document.createElement('button');btn.type='button';btn.className='smallbtn';
    btn.title=label;btn.setAttribute('aria-label',label);
    btn.style.cssText='width:48px;height:44px;padding:7px;display:grid;place-items:center';
    btn.innerHTML='<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+path+'</svg>';
    btn.onclick=callback;importButtons.append(btn);return btn;
  }
  importIcon('Import ingredients from link','<path d="M10 13a5 5 0 0 0 7.1 0l3-3a5 5 0 0 0-7.1-7.1l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.1 0l-3 3a5 5 0 0 0 7.1 7.1l1.7-1.7"/>',importGroceryFromLink);
  const photoInput=document.createElement('input');photoInput.type='file';photoInput.accept='image/*';photoInput.hidden=true;
  const cameraInput=document.createElement('input');cameraInput.type='file';cameraInput.accept='image/*';cameraInput.setAttribute('capture','environment');cameraInput.hidden=true;
  photoInput.onchange=e=>{const f=e.target.files?.[0];e.target.value='';if(f)importGroceryFromPhoto(f)};
  cameraInput.onchange=e=>{const f=e.target.files?.[0];e.target.value='';if(f)importGroceryFromPhoto(f)};
  importIcon('Import ingredients from photo','<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m3 17 5-5 4 4 3-3 6 6"/>',()=>photoInput.click());
  importIcon('Take photo of ingredients','<path d="M3 7h4l2-3h6l2 3h4v13H3z"/><circle cx="12" cy="13" r="4"/>',()=>cameraInput.click());
  importRow.append(photoInput,cameraInput);
  const actions=document.createElement('div');actions.style.cssText='display:flex;gap:5px;justify-content:space-between;flex-wrap:nowrap;margin-top:14px;width:100%;flex:0 0 auto';
  const selectAll=document.createElement('button');selectAll.className='smallbtn';selectAll.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="m7 12 3 3 7-7"/></svg>';selectAll.title='Select all';selectAll.setAttribute('aria-label','Select all');selectAll.onclick=()=>{checks.forEach(x=>x.cb.checked=true);rememberCheckedIngredients();renderIngredientRows()};
  const deselectAll=document.createElement('button');deselectAll.className='smallbtn';deselectAll.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7 12h10"/></svg>';deselectAll.title='Deselect all';deselectAll.setAttribute('aria-label','Deselect all');deselectAll.onclick=()=>{checks.forEach(x=>x.cb.checked=false);rememberCheckedIngredients();renderIngredientRows()};
  const deleteSelected=document.createElement('button');deleteSelected.type='button';deleteSelected.className='smallbtn';deleteSelected.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2m3 0-1 14H6L5 6m5 4v7m4-7v7"/></svg>';deleteSelected.title='Delete checked ingredients';deleteSelected.setAttribute('aria-label','Delete checked ingredients');deleteSelected.onclick=async()=>{const chosen=checks.filter(x=>x.cb.checked).map(x=>x.line);if(!chosen.length){await showAppMessage('Select ingredients to delete first.');return}if(!await appDialog('Delete '+chosen.length+' selected ingredient'+(chosen.length===1?'':'s')+' from this recipe?',null,'yesno')||!overlay.isConnected)return;const remove=new Set(chosen.map(ingredientKey));meal.ingredients=meal.ingredients.filter(line=>!remove.has(ingredientKey(line)));selectedByMeal[key]=checks.filter(x=>x.cb.checked&&!remove.has(ingredientKey(x.line))).map(x=>x.line);renderIngredientRows()};
  const cancel=document.createElement('button');cancel.className='smallbtn';cancel.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>';cancel.title='Cancel';cancel.setAttribute('aria-label','Cancel');
  const save=document.createElement('button');save.className='smallbtn';save.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l4 4L19 6"/></svg>';save.title='Save';save.setAttribute('aria-label','Save');save.onclick=()=>{snapshot();preserveGroceryCheckStates(groceryBefore);meal.ingredients=(Array.isArray(meal.ingredients)?meal.ingredients:[]).map(x=>String(x).trim()).filter(Boolean);const checkedLines=checks.filter(x=>x.cb.checked).map(x=>x.line);const previousSelections=new Set(originalSelected.map(ingredientKey));checkedLines.forEach(line=>{if(!previousSelections.has(ingredientKey(line))||manualReselections.has(ingredientKey(line)))checkedIngredients.delete(ingredientKey(line))});selectedByMeal[key]=checkedLines;for(const sibling of mealLinkedCopies(meal))selectedByMeal[String(sibling.id)]=[...checkedLines];meal.url=pendingRecipeUrl;meal.ingredientImportUrl=pendingIngredientImportUrl;fillMissingRecipeContent(meal,pendingRecipeDetails);assignSharedRecipeFields(meal,sharedRecipeChanges(originalRecipeRecord,meal));renamedIngredients.forEach(({from,to})=>{const oldKey=from.toLowerCase().replace(/\s+/g,' ').trim(),newKey=to.toLowerCase().replace(/\s+/g,' ').trim();if(checkedIngredients.has(oldKey))checkedIngredients.add(newKey)});try{localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selectedByMeal));localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));localStorage.setItem('mealRotationDataV1',JSON.stringify({cats,active,meals}))}catch(e){}renamedIngredients.forEach(({from,to})=>sharedRecipeMembers(meal).forEach(peer=>renameGrocerySourceChecks(peer,from,to)));uncheckGrocerySourceLines(meal,checkedLines.filter(line=>!previousSelections.has(ingredientKey(line))||manualReselections.has(ingredientKey(line))));saveGroceryOccurrenceChecks();persist();overlay.remove();renderList();if(pendingRecipeDetails?.recipeImportReferences?.length)recipeImportNotice('Related recipe references were found. No new links have been selected.',[meal])};
  let closeConfirmationOpen=false;
  async function requestClose(){const currentIngredients=(Array.isArray(meal.ingredients)?meal.ingredients:[]).map(x=>String(x).trim()).filter(Boolean);const currentSelected=checks.filter(x=>x.cb.checked).map(x=>x.line);const ingredientsChanged=JSON.stringify(currentIngredients)!==JSON.stringify(originalIngredients)||pendingRecipeUrl!==String(meal.url||'')||pendingIngredientImportUrl!==String(meal.ingredientImportUrl||'')||!!pendingRecipeDetails;const selectionsChanged=JSON.stringify([...currentSelected].sort())!==JSON.stringify([...originalSelected].filter(x=>currentIngredients.includes(x)).sort());if(!ingredientsChanged&&!selectionsChanged){overlay.remove();return}if(closeConfirmationOpen)return;closeConfirmationOpen=true;try{const shouldSave=await appDialog('Save changes before closing?',null,'yesno');if(!overlay.isConnected)return;if(shouldSave){save.click()}else{meal.ingredients=[...originalIngredients];selectedByMeal[key]=[...originalSelected];overlay.remove()}}finally{closeConfirmationOpen=false}}
  cancel.onclick=requestClose;
  [selectAll,deselectAll,deleteSelected,cancel,save].forEach(btn=>{btn.style.cssText='border:0;background:transparent;color:inherit;min-width:44px;min-height:44px;display:inline-flex;align-items:center;justify-content:center;padding:7px;cursor:pointer'});actions.append(selectAll,deselectAll,deleteSelected,save,cancel);
  box.append(title,list,addRow,importRow,actions);overlay.append(box);
  const chooserOpenedAt=Date.now();
  overlay.addEventListener('click',e=>{
    // Ignore the synthetic click generated when the finger that opened this
    // popup lifts. Otherwise the popup closes immediately on Android.
    if(e.target===overlay&&Date.now()-chooserOpenedAt>650)requestClose();
  });
  document.body.append(overlay)
}
function renderTopGroceries(list){
  const section=document.createElement('div');section.className='top-groceries';section.style.cssText='margin-top:24px;border-top:2px solid #bbb;padding-top:10px';
  const head=document.createElement('button');head.type='button';head.className='smallbtn';head.style.cssText='width:100%;display:flex;align-items:center;justify-content:space-between;font-size:18px;font-weight:400;padding:10px 12px;text-align:left';
  const body=document.createElement('div');body.style.marginTop='8px';
  const chosen=[];cats.forEach(c=>{const count=getTopCount(c);if(count>0)chosen.push(...meals.filter(m=>m.cat===c&&m.rotation).slice(0,count))});
  let selectedByMeal={};try{selectedByMeal=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}')}catch(e){}const ingredients=[];chosen.forEach(m=>{const mealKey=String(m.id);if(!Object.prototype.hasOwnProperty.call(selectedByMeal,mealKey)||!Array.isArray(selectedByMeal[mealKey]))return;const selectedSet=new Set(selectedByMeal[mealKey]);(Array.isArray(m.ingredients)?m.ingredients:[]).forEach(line=>{const clean=String(line).trim();if(clean&&selectedSet.has(clean))ingredients.push({line:clean,meal:m.name||'Untitled meal'})})});
  const groups=new Map();ingredients.forEach(item=>{const key=item.line.toLowerCase().replace(/\s+/g,' ').trim();if(!groups.has(key))groups.set(key,{line:item.line,meals:[]});groups.get(key).meals.push(item.meal)});
  const collapsed=localStorage.getItem('mealRotationGroceriesCollapsedV1')==='true';
  head.innerHTML='<span>Groceries</span><span aria-hidden="true">'+(collapsed?'＋':'−')+'</span>'; head.setAttribute('aria-expanded',String(!collapsed));body.classList.toggle('hidden',collapsed);head.onclick=()=>{const hide=!body.classList.contains('hidden');body.classList.toggle('hidden',hide);localStorage.setItem('mealRotationGroceriesCollapsedV1',String(hide));head.setAttribute('aria-expanded',String(!hide));head.lastElementChild.textContent=hide?'＋':'−'};section.append(head,body);
  let hideSelected=localStorage.getItem('mealRotationHideCheckedGroceriesV1')==='true';
  if(!groups.size){const p=document.createElement('p');p.className='muted';p.textContent='No groceries selected.';body.append(p)}else{
    groups.forEach((g,key)=>{if(hideSelected&&checkedIngredients.has(key))return;const row=document.createElement('label');row.className='shopmeal';row.style.cssText='display:flex;gap:10px;align-items:flex-start;padding:7px 2px;border-bottom:1px solid #eee';const cb=document.createElement('input');cb.type='checkbox';cb.checked=checkedIngredients.has(key);cb.onchange=()=>{snapshot();if(cb.checked)checkedIngredients.add(key);else checkedIngredients.delete(key);try{localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]))}catch(e){}renderList()};const text=document.createElement('span');text.textContent=g.line;text.style.cursor='pointer';text.title='Tap to see which recipes use this ingredient';text.onclick=e=>{e.preventDefault();e.stopPropagation();alert('Used in these top recipes:\n'+[...new Set(g.meals)].join('\n'))};row.append(cb,text);body.append(row)});
  }
  const controls=document.createElement('div');controls.style.cssText='display:flex;gap:14px;flex-wrap:wrap;justify-content:flex-end;margin:14px 2px 4px;font-size:12px;color:#666';
  const makeTextLink=(label,action)=>{const link=document.createElement('button');link.type='button';link.title=label;link.setAttribute('aria-label',label);link.innerHTML=label==='Select all'?'<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="m7 12 3 3 7-7"/></svg>':label==='Deselect all'?'<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7 12h10"/></svg>':label;link.style.cssText='cursor:pointer;border:0;background:transparent;color:#555;padding:4px;display:flex;align-items:center;justify-content:center';link.onclick=action;controls.append(link);return link};
  makeTextLink('Select all',()=>{snapshot();groups.forEach((g,key)=>checkedIngredients.add(key));try{localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]))}catch(e){}renderList()});
  makeTextLink('Deselect all',()=>{snapshot();groups.forEach((g,key)=>checkedIngredients.delete(key));try{localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]))}catch(e){}renderList()});
  makeTextLink(hideSelected?'Show selected':'Hide selected',()=>{hideSelected=!hideSelected;localStorage.setItem('mealRotationHideCheckedGroceriesV1',String(hideSelected));renderList()});
  const undoLink=document.createElement('span');undoLink.textContent='Undo';undoLink.style.cssText='cursor:pointer;text-decoration:none'+(groceryUndo?'':' ;opacity:.45;pointer-events:none');undoLink.onclick=()=>{if(!history.length)return;const target=JSON.parse(history.pop());redoHistory.push(captureHistoryCounterpart(target));restoreState(target)};controls.append(undoLink);body.append(controls);
  list.append(section);
}
// Ingredient import: read a public recipe page, preferring Recipe JSON-LD when available.
// Browsers cannot read many recipe sites directly because of CORS, so use public
// page-reading fallbacks. No API key, account data, or saved meals are transmitted.
// Some recipe page readers return Markdown task lists ("- [x] 1 cup flour").
// The checkbox is a website control, not part of the ingredient or quantity.
function removeIngredientListMarker(value){
  let line=String(value??'').trim();
  // Remove bullet + checklist, or a standalone checkbox, including checked and unchecked items.
  line=line.replace(/^(?:[-*+•–—]\s*)?(?:\[\s*(?:[xX✓✔]?)\s*\]|[☐☑☒✅✔✓])\s*/u,'');
  // Some structured recipe formats keep just the list bullet.
  line=line.replace(/^[-*+•–—]\s+(?=\S)/u,'');
  return line.trim();
}
function ingredientLine(value){
  if(value&&typeof value==='object'){
    if(typeof value.text==='string')value=value.text;
    else if(typeof value.name==='string')value=[value.value,value.unitText||value.unitCode,value.name].filter(x=>x!==undefined&&x!==null&&String(x).trim()).join(' ');
    else if(value.item)value=value.item;
    else return '';
  }
  return compactIngredientFractions(String(value??'').replace(/<[^>]*>/g,'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim());
}
// Format imported recipe quantities with compact Unicode fractions.
// Only change standalone quantity tokens; leave URLs, dates and ingredient names intact.
function uniqueIngredientLines(lines,limit=120){
  const seen=new Set();return lines.map(ingredientLine).filter(line=>{const k=line.toLowerCase();if(!line||seen.has(k))return false;seen.add(k);return true}).slice(0,limit);
}
function recipeIngredientsFromObject(obj){
  const recipes=[];const visited=new Set();
  function visit(value,depth=0){
    if(!value||typeof value!=='object'||depth>12||visited.has(value))return;
    visited.add(value);
    if(Array.isArray(value)){value.forEach(x=>visit(x,depth+1));return}
    const type=value['@type'];
    if((typeof type==='string'&&/(?:^|[:/])Recipe$/i.test(type))||(Array.isArray(type)&&type.some(x=>/(?:^|[:/])Recipe$/i.test(String(x))))){recipes.push(value)}
    for(const [k,v] of Object.entries(value))if(v&&typeof v==='object'&&['@graph','mainEntity','mainEntityOfPage','item','itemListElement','subjectOf','about','recipe'].includes(k))visit(v,depth+1);
  }
  visit(obj);
  for(const recipe of recipes){
    let raw=recipe.recipeIngredient??recipe.ingredients;
    if(raw&&typeof raw==='object'&&!Array.isArray(raw)&&Array.isArray(raw.itemListElement))raw=raw.itemListElement;
    const values=Array.isArray(raw)?raw:typeof raw==='string'?raw.split(/\r?\n/):raw?[raw]:[];
    const lines=uniqueIngredientLines(values);
    if(lines.length)return lines;
  }
  return [];
}
function recipeIngredientsFromMarkup(html){
  const doc=new DOMParser().parseFromString(html,'text/html');
  const jsonNodes=[...doc.querySelectorAll('script[type="application/ld+json"]')];
  for(const node of jsonNodes){
    try{const ingredients=recipeIngredientsFromObject(JSON.parse(node.textContent.trim()));if(ingredients.length)return ingredients}catch(e){}
  }
  const semantic=[...doc.querySelectorAll('[itemprop="recipeIngredient"], [itemprop="ingredients"]')];
  const semanticLines=uniqueIngredientLines(semantic.map(el=>el.getAttribute('content')||el.textContent));
  if(semanticLines.length)return semanticLines;
  const selectors=['[data-ingredient-name]','[data-testid="ingredient-list"] li','[class*="ingredient-list"] li','[class*="ingredients-list"] li','[class*="recipe-ingredient"] li','li[class*="ingredient"]','[class*="wprm-recipe-ingredient"]'];
  for(const selector of selectors){
    const nodes=[...doc.querySelectorAll(selector)];
    const lines=uniqueIngredientLines(nodes.map(el=>el.getAttribute('data-ingredient-name')||el.textContent));
    if(lines.length>=2)return lines;
  }
  return [];
}
function recipeIngredientsFromMarkdown(markdown){
  const source=String(markdown).split(/\r?\n/).slice(0,12000);
  let best=[];
  for(let i=0;i<source.length;i++){
    const heading=source[i].trim().replace(/^#{1,6}\s*/, '').replace(/\*\*/g,'').replace(/:$/,'').trim();
    if(!/^ingredients(?:\s+for\s+.{1,50})?$/i.test(heading))continue;
    const candidates=[];let seenItem=false;
    for(let j=i+1;j<Math.min(source.length,i+135);j++){
      const line=source[j].trim();
      if(/^#{1,6}\s/.test(line)&&seenItem)break;
      if(/^(?:directions|instructions|method|steps|preparation|nutrition|notes|equipment|reviews|you(?:'|’)ll need|how to make|print recipe|related recipes)\b/i.test(line.replace(/^#{1,6}\s*/,''))&&seenItem)break;
      if(!line){if(seenItem&&source.slice(j+1,j+4).every(x=>!x.trim()))break;continue}
      if(/^\*\*[\d./¼½¾⅓⅔⅛⅜⅝⅞]+\*\*\s+\S/.test(line)){candidates.push(line.replace(/\*\*/g,''));seenItem=true}
      else if(/^[-*+]\s+/.test(line)||/^\d+[.)]\s+/.test(line)){
        const item=line.replace(/^(?:[-*+]\s+|\d+[.)]\s+)/,'').replace(/^\[[ xX]\]\s*/, '').replace(/\*\*/g,'').replace(/\[([^\]]+)\]\([^)]*\)/g,'$1').trim();
        if(item&&!/^(?:image|video|pin it|save|print)$/i.test(item)){candidates.push(item);seenItem=true}
      }else if(seenItem&&/^\s*(?:[-–]|[0-9]|[¼½¾⅓⅔]|\d+\s*(?:cup|tbsp|tsp|oz|lb|g|ml|clove|pinch))/.test(line)&&!/^\d+\.\s+(?:preheat|heat|stir|mix|bake|cook|place)\b/i.test(line)){
        candidates.push(line.replace(/^[-–]\s*/,''));
      }else if(seenItem&&/^(?:\w+[\s'-]*){1,6}:$/.test(line)){continue}
      else if(seenItem)break;
    }
    const lines=uniqueIngredientLines(candidates);
    if(lines.length>best.length)best=lines;
  }
  return best.length>=2?best:[];
}
function extractRecipeIngredients(payload){
  const value=String(payload||'').trim();if(!value)return [];
  if(value[0]==='{'||value[0]==='['){
    try{const obj=JSON.parse(value);const direct=recipeIngredientsFromObject(obj);if(direct.length)return direct;
      if(typeof obj?.data?.content==='string')return extractRecipeIngredients(obj.data.content);
      if(typeof obj?.contents==='string')return extractRecipeIngredients(obj.contents);
      if(typeof obj?.content==='string')return extractRecipeIngredients(obj.content);
    }catch(e){}
  }
  if(/<!doctype|<html|application\/ld\+json|itemprop=|class=["'][^"']*ingredient/i.test(value)){
    const lines=recipeIngredientsFromMarkup(value);if(lines.length)return lines;
  }
  return recipeIngredientsFromMarkdown(value);
}
async function importIngredientsFromWebsite(value,externalSignal,expectedName=''){
 let parsed;try{parsed=new URL(value)}catch(e){throw Error('Enter a valid recipe URL to import ingredients.')}
 if(!['http:','https:'].includes(parsed.protocol))throw Error('Enter a valid website URL.');
 const address=parsed.href,readers=['https://api.allorigins.win/raw?url='+encodeURIComponent(address),'https://r.jina.ai/'+address];
 async function request(endpoint,limit=14000){
  const controller=new AbortController(),abort=()=>controller.abort();if(externalSignal?.aborted)controller.abort();externalSignal?.addEventListener('abort',abort,{once:true});const timer=setTimeout(abort,limit);
  try{
   const response=await fetch(endpoint,{signal:controller.signal,credentials:'omit'});if(!response.ok)throw Error('The recipe website could not be read.');const raw=await response.text();if(raw.length>2500000)throw Error('Recipe page too large.');
   const details=extractCompleteRecipe(raw,address,expectedName),ingredients=details?.ingredients?.length?uniqueIngredientLines(details.ingredients,Infinity):extractRecipeIngredients(raw);
   if(!ingredients.length&&!details?.instructions?.some(block=>block.type==='step'))throw Error('No supported recipe details found.');
   ingredients.recipeDetails=details;return ingredients;
  }finally{clearTimeout(timer);externalSignal?.removeEventListener('abort',abort)}
 }
 const complete=result=>result?.recipeDetails?.instructions?.some(block=>block.type==='step');let partial=null;
 if(parsed.protocol==='https:'){try{const result=await request(address,4500);if(complete(result))return result;partial=result}catch(e){if(externalSignal?.aborted)throw e}}
 if(externalSignal?.aborted)throw Error('Recipe import cancelled.');
 const results=await Promise.allSettled(readers.map(endpoint=>request(endpoint)));
 if(externalSignal?.aborted)throw Error('Recipe import cancelled.');
 const successes=results.filter(result=>result.status==='fulfilled').map(result=>result.value);
 const best=successes.find(complete)||partial||successes[0];
 if(!best)throw Error('Recipe details could not be imported from this website. Your saved recipe is unchanged; you can add instructions manually.');
 if(!best.length&&partial?.length){const details={...best.recipeDetails,ingredients:[...partial]};const combined=[...partial];combined.recipeDetails=details;return combined}
 if(!complete(best)&&best.recipeDetails)best.recipeDetails.instructionWarning='Ingredients were retrieved, but reliable cooking instructions were unavailable. Retry from the saved URL or add them manually.';
 return best;
}
function showImportProgressDialog(message="Importing ingredients from website…"){
  const controller=new AbortController();
  let resolveCancel;
  const cancelled=new Promise(resolve=>{resolveCancel=()=>resolve({cancelled:true})});
  const overlay=document.createElement('div');
  overlay.style.cssText='position:fixed;inset:0;z-index:13020;background:#0008;display:flex;align-items:center;justify-content:center;padding:18px';
  const panel=document.createElement('div');
  panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Import ingredients');
  panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:22px;width:100%;max-width:480px;box-shadow:0 12px 36px #0003';
  const heading=document.createElement('div');
  heading.textContent=message;
  heading.setAttribute('role','status');heading.style.cssText='font-size:19px;font-weight:600;margin-bottom:18px';
  const actions=document.createElement('div');actions.style.cssText='display:flex;gap:12px;justify-content:center';
  const cancel=document.createElement('button');cancel.type='button';cancel.className='smallbtn';
  cancel.title='Cancel import';cancel.setAttribute('aria-label','Cancel ingredient import');
  cancel.style.cssText='min-width:56px;min-height:46px;display:grid;place-items:center;padding:9px 14px';
  cancel.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>';
  const stop=()=>{resolveCancel();controller.abort();overlay.remove()};
  cancel.onclick=stop;
  const onKey=e=>{if(e.key==='Escape'){e.preventDefault();stop()}};
  overlay.addEventListener('keydown',onKey);
  actions.append(cancel);panel.append(heading,actions);overlay.append(panel);document.body.append(overlay);
  cancel.focus({preventScroll:true});
  return {signal:controller.signal,cancelled,abort:()=>controller.abort(),close:()=>overlay.remove()};
}
function showAppMessage(message){
  return new Promise(resolve=>{
    const overlay=document.createElement('div');
    overlay.style.cssText='position:fixed;inset:0;z-index:13021;background:#0008;display:flex;align-items:center;justify-content:center;padding:18px';
    const panel=document.createElement('div');panel.setAttribute('role','alertdialog');panel.setAttribute('aria-modal','true');
    panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:22px;width:100%;max-width:480px;box-shadow:0 12px 36px #0003';
    const heading=document.createElement('div');heading.textContent=message;
    heading.style.cssText='font-size:19px;font-weight:600;margin-bottom:18px';
    const actions=document.createElement('div');actions.style.cssText='display:flex;gap:12px;justify-content:center';
    const ok=document.createElement('button');ok.type='button';ok.className='smallbtn';ok.textContent='OK';
    ok.style.cssText='min-width:100px;padding:11px 20px';
    ok.onclick=()=>{overlay.remove();resolve()};
    actions.append(ok);panel.append(heading,actions);overlay.append(panel);if(recipeViewer)overlay.style.zIndex='31000';if(document.querySelector('.recipe-bulk-dialog'))overlay.style.zIndex='37000';document.body.append(overlay);
    ok.focus({preventScroll:true});
  });
}
// Load photo text recognition only when the user chooses a photo/camera.
let ingredientOcrLoader=null;
function getIngredientOcr(){
  if(window.Tesseract)return Promise.resolve(window.Tesseract);
  if(!ingredientOcrLoader){
    ingredientOcrLoader=new Promise((resolve,reject)=>{
      const script=document.createElement('script');script.async=true;
      script.src='https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js';
      let finished=false;
      const settle=(error)=>{
        if(finished)return;
        finished=true;clearTimeout(timeout);
        if(error){script.remove();reject(error)}
        else resolve(window.Tesseract);
      };
      const timeout=setTimeout(()=>settle(Error('Photo text reader could not load. Check your connection and try again.')),25000);
      script.onload=()=>settle(window.Tesseract?null:Error('Photo reader unavailable.'));
      script.onerror=()=>settle(Error('Could not load the photo text reader. Check your internet connection.'));
      document.head.append(script);
    }).catch(e=>{ingredientOcrLoader=null;throw e});
  }
  return ingredientOcrLoader;
}
// Quickly recognize nearly uniform photographs without starting OCR. This
// avoids spending minutes trying to read an image with no visible writing.
async function ingredientPhotoIsBlank(file){
  if(typeof createImageBitmap!=='function')return false;
  let bitmap;
  try{
    bitmap=await createImageBitmap(file,{resizeWidth:80,resizeHeight:80,resizeQuality:'low'});
    const canvas=document.createElement('canvas');canvas.width=80;canvas.height=80;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});if(!ctx)return false;
    ctx.drawImage(bitmap,0,0,80,80);
    const pixels=ctx.getImageData(0,0,80,80).data;
    let sum=0,sumSquares=0,low=255,high=0,count=0;
    for(let i=0;i<pixels.length;i+=4){
      if(pixels[i+3]<24)continue;
      const lum=(pixels[i]*299+pixels[i+1]*587+pixels[i+2]*114)/1000;
      sum+=lum;sumSquares+=lum*lum;low=Math.min(low,lum);high=Math.max(high,lum);count++;
    }
    if(!count)return true;
    const variance=Math.max(0,sumSquares/count-(sum/count)**2);
    return Math.sqrt(variance)<4.5&&high-low<40;
  }catch(e){return false}
  finally{if(bitmap)bitmap.close()}
}
// Light text on a dark app screen is difficult for mobile OCR. Present a
// high-contrast copy to the reader, without modifying or uploading the photo.
async function prepareIngredientPhotoForOcr(file){
  if(typeof createImageBitmap!=='function')return file;
  let bitmap;
  try{
    bitmap=await createImageBitmap(file);
    const w=bitmap.width,h=bitmap.height;
    if(!w||!h)return file;
    const sample=document.createElement('canvas');sample.width=48;sample.height=48;
    const sc=sample.getContext('2d',{willReadFrequently:true});if(!sc)return file;
    sc.drawImage(bitmap,0,0,48,48);
    const data=sc.getImageData(0,0,48,48).data;
    let dark=0,n=0;
    for(let i=0;i<data.length;i+=4){
      if(data[i+3]<50)continue;
      if((data[i]*.299+data[i+1]*.587+data[i+2]*.114)<105)dark++;
      n++;
    }
    if(!n||dark/n<.57)return file; // Keep ordinary paper/photos unchanged.
    const canvas=document.createElement('canvas');
    const scale=Math.min(1.5,1900/Math.max(w,h));
    canvas.width=Math.max(1,Math.round(w*scale));canvas.height=Math.max(1,Math.round(h*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});if(!ctx)return file;
    ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
    const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
    for(let i=0;i<pixels.data.length;i+=4){
      const lum=pixels.data[i]*.299+pixels.data[i+1]*.587+pixels.data[i+2]*.114;
      // Ink becomes black, background white. Preserve enough anti-aliasing
      // to read thin characters and fractions.
      const grey=Math.max(0,Math.min(255,255-(lum-65)*2.9));
      pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=grey;
    }
    ctx.putImageData(pixels,0,0);
    return canvas;
  }catch(e){return file}
  finally{if(bitmap)bitmap.close()}
}
// A dedicated worker can be terminated if OCR is cancelled or times out.
async function recognizeIngredientPhoto(file,signal){
  const ocr=await getIngredientOcr();
  if(signal.aborted)return '';
  const input=await prepareIngredientPhotoForOcr(file);
  if(signal.aborted)return '';
  if(typeof ocr.createWorker!=='function'){
    const result=await ocr.recognize(input,'eng');
    return signal.aborted?'':(result?.data?.text||'');
  }
  let worker=null;
  const stopWorker=()=>{if(worker)Promise.resolve(worker.terminate()).catch(()=>{})};
  signal.addEventListener('abort',stopWorker,{once:true});
  try{
    worker=await ocr.createWorker('eng');
    if(signal.aborted)return '';
    const result=await worker.recognize(input);
    return signal.aborted?'':(result?.data?.text||'');
  }finally{
    signal.removeEventListener('abort',stopWorker);
    stopWorker();
  }
}
function ingredientDialog(title,build){
  const shade=document.createElement('div');
  shade.style.cssText='position:fixed;inset:0;z-index:13025;background:#0008;display:flex;align-items:center;justify-content:center;padding:18px';
  const panel=document.createElement('div');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');
  panel.setAttribute('aria-label',title);panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:22px;width:100%;max-width:480px;max-height:85vh;overflow-y:auto;box-shadow:0 12px 36px #0003';
  const heading=document.createElement('div');heading.textContent=title;heading.style.cssText='font-size:19px;font-weight:600;margin-bottom:16px';panel.append(heading);
  const close=()=>shade.remove();build(panel,close);shade.append(panel);document.body.append(shade);
  return {close,panel};
}
function ingredientModalButton(label,onClick){
  const b=document.createElement('button');b.type='button';b.className='smallbtn';b.textContent=label;
  b.style.cssText='min-height:44px;padding:10px 14px;font-size:15px';b.onclick=onClick;return b;
}
function selectIngredientImportSource(hasRecipeUrl){
  return new Promise(resolve=>{
    ingredientDialog('Import ingredients from link',(panel,close)=>{
      const controls=document.createElement('div');controls.style.cssText='display:flex;flex-direction:column;gap:10px';
      const choose=(label,value)=>ingredientModalButton(label,()=>{close();resolve(value)});
      const fromRecipe=choose('Import from recipe link','recipe');fromRecipe.disabled=!hasRecipeUrl;
      controls.append(fromRecipe,choose('Use a different link','other'),choose('Cancel',null));
      if(!hasRecipeUrl){const hint=document.createElement('div');hint.className='muted';hint.textContent='No recipe link. Choose an ingredient source.';panel.append(hint)}
      panel.append(controls);
    });
  });
}
function requestIngredientSourceUrl(previous,hasRecipeUrl=true){
  return new Promise(resolve=>{
    ingredientDialog('Import ingredients from link',(panel,close)=>{
      const field=document.createElement('input');field.type='url';field.placeholder='https://';field.value=previous||'';
      field.style.cssText='display:block;width:100%;padding:11px;border:1px solid #ccc;border-radius:9px;margin-bottom:15px;font-size:16px';panel.append(field);
      const actions=document.createElement('div');actions.style.cssText='display:flex;gap:10px;justify-content:center';
      const submit=()=>{const url=field.value.trim();try{const parsed=new URL(url);if(!['https:','http:'].includes(parsed.protocol))throw Error()}catch(e){field.setCustomValidity('Enter a valid website link.');field.reportValidity();return}field.setCustomValidity('');close();resolve(url)};
      field.oninput=()=>field.setCustomValidity('');field.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();submit()}};
      actions.append(ingredientModalButton('Import',submit),ingredientModalButton('Cancel',()=>{close();resolve(null)}));panel.append(actions);
    });
  });
}
function askUseIngredientLinkAsRecipe(){
  return new Promise(resolve=>{
    ingredientDialog('Save recipe link?',(panel,close)=>{
      const question=document.createElement('p');
      question.textContent='Use this as the recipe link?';
      question.style.cssText='font-size:16px;margin:0 0 16px';panel.append(question);
      const actions=document.createElement('div');actions.style.cssText='display:flex;gap:12px;justify-content:center';
      actions.append(
        ingredientModalButton('Yes',()=>{close();resolve(true)}),
        ingredientModalButton('No',()=>{close();resolve(false)})
      );
      panel.append(actions);
    });
  });
}
// Clean photo OCR before asking the user to review it. This runs locally in the browser.
// It deliberately favors omission of uncertain page text over inventing ingredients.
function cleanPhotoIngredientLine(value){
  let line=String(value||'').replace(/[\u00a0\u2000-\u200b]/g,' ').trim();
  // OCR often reads an empty checkbox as "(J", "[]", a bullet or a circled glyph.
  for(let n=0;n<3;n++){
    const cleaned=line.replace(/^(?:(?:\[\s*\]|\(\s*[JjVvUu✓✔]?\s*\)?|[☐☑☒□▢◻◯○✓✔•●])\s*|[-–*]\s+|[|¦]\s*)/u,'').trim();
    if(cleaned===line)break;
    line=cleaned;
  }
  line=line.replace(/^[()\[\]{}]+\s*/,'').trim();
  // Fix common OCR mistakes such as "3Tbsp.unsalted" and "1cup (235ml.)".
  line=line.replace(/^([Il|])\s+(?=(?:cups?|tbsp\.?|tsp\.?|tablespoons?|teaspoons?|lbs?|pounds?|oz\.?|ounces?|eggs?|cloves?)\b)/i,'1 ');
  line=line.replace(/(\d|[¼½¾⅓⅔⅛⅜⅝⅞])(?=[a-z])/gi,'$1 ');
  line=line.replace(/(\d)\s*([¼½¾⅓⅔⅛⅜⅝⅞])/g,'$1 $2');
  line=line.replace(/\b(tbsp|tsp)\.(?=[a-z])/gi,'$1. ');
  line=line.replace(/\b(ml|g|kg|oz|lb)\.(?=[a-z])/gi,'$1. ');
  // Restore word boundaries missed by OCR in ingredient quantities:
  // "1cup(120 g.)" -> "1 cup (120 g.)", including a space after conversions.
  line=line.replace(/([a-z])\s*\((?=\s*\d)/gi,'$1 (');
  line=line.replace(/\)(?=[a-z])/gi,') ');
  // A short, conservative list of common adjacent ingredient words that OCR
  // sometimes merges. Avoid splitting arbitrary valid ingredient names.
  line=line.replace(/\b(kosher|sea|table)(?=salt\b)/gi,'$1 ');
  line=line.replace(/\b(granulated|brown|powdered|caster)(?=sugar\b)/gi,'$1 ');
  line=line.replace(/\b(unsalted|salted)(?=butter\b)/gi,'$1 ');
  line=line.replace(/\b(whole|skim)(?=milk\b)/gi,'$1 ');
  line=line.replace(/\b(black|white)(?=pepper\b)/gi,'$1 ');
  line=line.replace(/\b(baking)(?=(?:powder|soda)\b)/gi,'$1 ');
  line=line.replace(/\b(olive|vegetable|coconut)(?=oil\b)/gi,'$1 ');
  line=line.replace(/\s+([,.])/g,'$1').replace(/([,;])(?=\S)/g,'$1 ');
  line=line.replace(/\s{2,}/g,' ').trim();
  return compactIngredientFractions(line);
}
// Remove instructions about handling/temperature from imported ingredients.
// Keep quantities, ingredient varieties (e.g. unsalted, whole, frozen) and
// shopping-relevant cuts or sizes (e.g. diced, minced, thinly sliced).
// Only automatic imports are cleaned: manually typed/reviewed wording is kept.
function cleanImportedIngredientDescriptors(value){
  let line=removeIngredientListMarker(ingredientLine(value));
  if(!line)return '';
  const temp='(?:at\\s+|brought\\s+to\\s+)?room[\\s-]+temp(?:erature)?';
  const preparation='(?:'+temp+'|divided(?:\\s+into\\s+\\d+\\s+(?:parts?|portions?|batches?))?|softened|melted|thawed|cooled(?:\\s+slightly)?|chilled|warmed|lightly\\s+beaten|well\\s+beaten|beaten(?:\\s+lightly)?|whisked|peeled|seeded|de-?seeded|cored|stemmed|de-?veined|rinsed|well[\\s-]+drained|un-?drained|drained|washed|sifted|toasted|blanched|well\\s+shaken|shaken|stirred|scrubbed|stems?\\s+removed|spooned\\s+and\\s+leveled|patted\\s+dry|patted\\s+down|brought\\s+to\\s+a\\s+boil|separated)';
  // Parenthetical temperature/prep notes, but not quantity conversions like (235 ml).
  const prepParentheses=new RegExp('\\s*\\(\\s*(?:'+preparation+'|optional|for\\s+(?:serving|garnish|garnishing)|to\\s+taste)\\s*\\)','gi');
  line=line.replace(prepParentheses,'');
  // Strip serving and usage notes at the end without altering the ingredient name.
  line=line.replace(/(?:\s*[,;]?\s*(?:plus\s+(?:more|extra)(?:\s+[^,;]*)?|for\s+(?:serving|garnish(?:ing)?|dusting|greasing|drizzling|topping|brushing)(?:\s+[^,;]*)?|to\s+taste|as\s+needed|if\s+desired|optional))\s*$/i,'');
  const prep=new RegExp('\\b'+preparation+'\\b','gi');
  // First remove unwanted descriptors, preserving adjacent preparation cuts.
  line=line.replace(prep,'');
  // Also remove standalone temperature notes such as ', cold' or ', hot'.
  line=line.replace(/[,;]\s*(?:very\s+)?(?:ice[\s-]*cold|cold|hot|warm|lukewarm|boiling)\s*(?=[,;]|$)/gi,'');
  // Temperature adjectives directly modifying cooking liquids/eggs/butter.
  // Do not alter product descriptions such as "hot sauce" or "frozen peas".
  line=line.replace(/\b(?:ice[\s-]*cold|lukewarm|boiling|very\s+cold|cold|hot|warm)\s+(?=(?:water|milk|eggs?|butter|broth|stock|cream|juice)\b)/gi,'');
  // Clean punctuation left by removed phrases: ", and diced" -> ", diced".
  line=line.replace(/\s+,\s*,/g,',').replace(/,\s*(?:and\s+)?(?=,|;|$)/gi,'');
  line=line.replace(/,\s*and\s+/gi,', ').replace(/\s+and\s*(?=,|;|$)/gi,'');
  line=line.replace(/\s*[,;]\s*[,;]+/g,', ').replace(/\s*[,;]\s*$/,'');
  line=line.replace(/\(\s*(?:(?:and|or)\s*)?\)/gi,'').replace(/\s{2,}/g,' ').replace(/\s+([,;])/g,'$1').replace(/\s*[,;]\s*$/,'').trim();
  return line;
}
function extractPhotoIngredientLines(raw){
  // Only the ingredient section should reach the grocery list. Work on
  // original OCR rows so that wrapped ingredients can be reassembled first.
  const original=String(raw||'').replace(/\r\n?/g,'\n');
  const rows=original.split('\n').map(cleanPhotoIngredientLine).filter(Boolean);
  // OCR can read the icon beside 'Ingredients' as stray letters (e.g. 'ina Ingredients').
  const heading=/^(?:(?:the|[a-z]{1,5})\s+)?ingredients?(?:\s*[:：.]|\s*\([^)]*\))?\s*$/i;
  const headingIndex=rows.findIndex(x=>heading.test(x));
  const candidates=headingIndex<0?rows:rows.slice(headingIndex+1);
  const stop=/^(?:directions?|instructions?|instruct[il1]ons?|method|preparation|steps?|how to (?:make|cook|prepare)|recipe notes?|notes for this recipe|nutrition(?:al)?(?:\s+(?:information|facts|info))?|keep (?:the )?screen awake|shop recipe|shop ingredients|shop the recipe|related recipes|you may also like|comments?|reviews?|rate (?:this|the) recipe|frequently asked questions|advertisement|sponsored|video|watch video|print recipe|recipe card)\b/i;
  const scale=/^(?:\d+\s*[x×]\s*scale\b|(?:scale\s*[:·•-]?\s*)?original(?:\s*(?:size|scale))?$|\d+\s*[x×]\s*(?:original|metric)\b)/i;
  const noise=/^(?:save|print|i made it|made it|share|download|get it on|app store|google play|play store|see all nutrition|see nutritional|jump to recipe|skip to recipe|back to top|search|follow us|sign up|subscribe|log in|login|rating|rate it|cook mode|servings?|yield|author|total time|prep time|cook time|calories|reviews?|view recipe|add to cart|shop|select all|metric|us customary|cost|recipe by|read more|more information)\b/i;
  const section=/^(?:(?:for\s+the\s+)?(?:marinade|sauce|garnish|topping|filling|dough|batter|dry\s+ingredients?|wet\s+ingredients?|optional\s+ingredients?|for\s+serving|for\s+the\s+marinade|for\s+the\s+sauce))\s*:?$/i;
  // Include quantity ranges ("2 - 3 TBSP"), fractions and item counts.
  const qty=/^(?:(?:\d+(?:[.,]\d+)?|\d+\s*\/\s*\d+|[¼½¾⅓⅔⅛⅜⅝⅞])(?:\s*(?:-|–|—|to)\s*(?:\d+(?:[.,]\d+)?|\d+\s*\/\s*\d+|[¼½¾⅓⅔⅛⅜⅝⅞]))?(?:\s+(?:\d+\s*\/\s*\d+|[¼½¾⅓⅔⅛⅜⅝⅞]))?|one|two|three|four|five|six|seven|eight|nine|ten|a|an|pinch|dash|handful)(?:\s+|(?=[a-z]))/i;
  const cookStep=/^(?:(?:\d+\s*[.)]?\s*)?)(?:preheat|pound(?:\s+or\s+mash)?|mash|bake|roast|heat|whisk|stir|combine|mix|add\b|cook|pour|place|set aside|transfer|bring\s+to|boil|simmer|serve|remove|cover|refrigerate|whip|beat|grease|line\s+a|fold|knead|let\s+sit|allow\s+to)\b/i;
  const results=[];
  let ended=false;
  function openParentheses(line){return (line.match(/\(/g)||[]).length>(line.match(/\)/g)||[]).length}
  for(let i=0;i<candidates.length;i++){
    let entry=candidates[i];
    // A numbered instruction is not an amount of an ingredient. Treat it as
    // the start of the method even if OCR missed the Instructions heading.
    if(stop.test(entry)||scale.test(entry)||(/^(?:\d+\s+|\d+\s*[.)]\s*)/.test(entry)&&cookStep.test(entry)&&results.length>=1)){
      ended=true;break;
    }
    if(section.test(entry)||heading.test(entry))continue; // "MARINADE" is a group, not an ingredient.
    if(noise.test(entry)||/https?:\/\/|www\.|@|©|®|\b(?:app store|google play|download|print|rating|stars|subscribe|privacy policy|cookie|affiliate|advertis|copyright|replies)\b/i.test(entry))continue;
    if(/^\d{1,2}:\d{2}\b/.test(entry)||/[#<>]/.test(entry)||/^[^a-zA-Z]*$/.test(entry))continue;
    if(cookStep.test(entry)||/[!?]$/.test(entry))continue;
    // "Optional: 1 tsp cornstarch" is an ingredient, not a heading.
    entry=entry.replace(/^optional\s*[:\-]\s*/i,'').trim();
    if(!entry)continue;
    if(entry.length>190||entry.split(/\s+/).length>29)continue;
    const hasAmount=qty.test(entry);
    const prior=results[results.length-1];
    if(prior){
      // A line may wrap after a hyphen ("bite- / size"), inside alternatives
      // ("coconut aminos / and 1/2 tsp salt"), or inside parentheses.
      const hyphenWrap=/[-‐‑‒–—]$/.test(prior);
      const trailing=/[,;(]$|\b(?:and|or|to|of|at|for|plus|with|a|an|the|thin|bite|finely|roughly|freshly)$/i.test(prior);
      const lead=/^(?:and|or|of|to|with|in|for|size\b|pieces?\b|the\b|\))/i.test(entry);
      if(hyphenWrap||openParentheses(prior)||(!hasAmount&&(trailing||lead))){
        results[results.length-1]=hyphenWrap?prior+entry:prior+' '+entry;
        continue;
      }
    }
    // Even if the title was unreadable, keep a short, quantity-free item
    // embedded among known ingredients, such as 'Lime wedges' or 'Fresh basil'.
    // Do not accept unrelated introductory text before the first ingredients.
    if(!hasAmount&&headingIndex<0){
      const words=entry.split(/\s+/);
      const nearbyIngredient=results.some(x=>qty.test(x))&&
        candidates.slice(i+1,i+4).some(x=>qty.test(x.replace(/^optional\s*[:\-]\s*/i,''))||section.test(x));
      const ingredientPhrase=words.length<=5&&/^[a-z][a-z\s,'’\-/]*$/i.test(entry)&&
        !/^(?:this|these|those|you|your|my|our|try|use|recipe|delicious|perfect|all|more|made|good|ready|next)\b/i.test(entry);
      if(!nearbyIngredient||!ingredientPhrase)continue;
    }
    if(!hasAmount&&(entry.split(/\s+/).length>10||/^\d+\s*[x×]\s*scale/i.test(entry)))continue;
    results.push(entry);
  }
  const lines=uniqueIngredientLines(results.map(x=>cleanImportedIngredientDescriptors(
    // Standardize range spacing; don't change individual quantities.
    x.replace(/\b(\d+)\s*[-–—]\s*(\d+)\s+(?=(?:tbsp|tsp|cloves?|cups?|lbs?|oz|g|kg|pieces?)\b)/gi,'$1–$2 ')
  )));
  return {lines,hadHeading:headingIndex>=0,removedLines:Math.max(0,rows.length-results.length),ended};
}
function reviewPhotoIngredients(text,originalText,kind='ingredients'){
  return new Promise(resolve=>{
    ingredientDialog(kind==='instructions'?'Review photo cooking instructions':'Review photo ingredients',(panel,close)=>{
      const hint=document.createElement('div');hint.textContent=kind==='instructions'?'Review and correct the cooking instructions before applying them.':'Check ingredients before adding.';
      hint.style.cssText='font-size:14px;color:#666;margin-bottom:10px';panel.append(hint);
      const area=document.createElement('textarea');area.className='ingredients-input';area.value=text;area.setAttribute('aria-label',kind==='instructions'?'Reviewed cooking instructions':'Reviewed ingredients');
      area.style.cssText='width:100%;min-height:185px;margin-bottom:12px';panel.append(area);
      // Keep the raw scan available in case the automatic filter omitted a line.
      if(originalText&&String(originalText).trim()!==String(text).trim()){
        const details=document.createElement('details');details.style.cssText='margin:0 0 16px;font-size:14px;color:#555';
        const summary=document.createElement('summary');summary.textContent='View original scanned text';summary.style.cssText='cursor:pointer;padding:5px 0';
        const raw=document.createElement('textarea');raw.readOnly=true;raw.className='ingredients-input';raw.value=originalText;
        raw.setAttribute('aria-label','Original scanned text');raw.style.cssText='width:100%;min-height:110px;margin-top:8px;font-size:14px';
        details.append(summary,raw);panel.append(details);
      }
      const actions=document.createElement('div');actions.style.cssText='display:flex;gap:10px;justify-content:center;flex-wrap:wrap';
      actions.append(ingredientModalButton(kind==='instructions'?'Use instructions':'Add ingredients',()=>{close();resolve(area.value)}),ingredientModalButton('Cancel',()=>{close();resolve(null)}));panel.append(actions);
    });
  });
}
const RECIPE_EDITOR_SECTIONS_KEY='mealRotationEditorSectionsV1';
let recipeEditorSections={ingredients:false,instructions:false},recipeEditorReturn=null;
function addRecipeEditorSourceLink(field){
 const row=document.createElement('div');row.style.cssText='display:flex;align-items:center;gap:8px';
 const link=document.createElement('a');link.textContent='Original recipe';link.target='_blank';link.rel='noopener noreferrer';
 const edit=document.createElement('button');edit.type='button';edit.className='ingredient-tool';edit.style.cssText='width:30px;height:30px;flex:0 0 30px;padding:5px';setRecipeToolbarIcon(edit,'edit','Edit recipe URL');edit.querySelector('svg').style.cssText='width:18px;height:18px';
 field.before(row);row.append(link,edit);field.hidden=true;if(field.parentElement.tagName==='LABEL')field.parentElement.querySelector('span')?.setAttribute('hidden','');
 const previous=row.previousElementSibling;if(previous?.tagName==='LABEL'){field.setAttribute('aria-label',previous.textContent);previous.remove()}
 edit.onclick=()=>{field.hidden=!field.hidden;if(!field.hidden)field.focus({preventScroll:true})};
 const update=()=>{let url;try{url=new URL(field.value.trim())}catch(_){}const valid=url&&['http:','https:'].includes(url.protocol);link.hidden=!valid;edit.setAttribute('aria-label',valid?'Edit recipe URL':'Add recipe URL');edit.title=edit.getAttribute('aria-label');if(valid)link.href=url.href;else link.removeAttribute('href')};
 field.addEventListener('input',update);update();return link;
}
function collapseRecipeEditorField(field,title){
 const label=field.parentElement,details=document.createElement('details'),summary=document.createElement('summary');
 details.className='settings-group';details.open=true;summary.textContent=title;label.before(details);details.append(summary,label);label.querySelector('span')?.remove();return details;
}
function openViewedRecipeEditor(){
 const view=recipeViewer;if(!view)return;
 if(view.linkEdit){recipeLinkMessage(view,'Save or cancel the current ingredient links before editing the recipe.');return}
 const meal=meals.find(m=>String(m.id)===view.mealId);if(!meal||document.querySelector('[data-viewer-recipe-draft]'))return;
 captureRecipeTab(view);cancelRecipeAdvance(view);view.importController?.abort();
 const original=JSON.parse(JSON.stringify(meal)),d=recipeBulkDialog('Edit Recipe'),fields=document.createElement('div');fields.className='recipe-bulk-fields';d.panel.append(fields);
 const ingredients=stage2FormField(fields,'Ingredients',document.createElement('textarea'));ingredients.rows=5;ingredients.value=(meal.ingredients||[]).join('\n');
 const instructions=stage2FormField(fields,'Steps',document.createElement('textarea'));instructions.rows=6;instructions.value=instructionEditorText(meal.instructions);
 const url=stage2FormField(fields,'Recipe source link',document.createElement('input'));url.type='url';url.value=recipeDisplaySourceUrl(meal);
 const notes=stage2FormField(fields,'Recipe notes',document.createElement('textarea'));notes.rows=3;notes.value=String(meal.notes||'');
 ingredients.placeholder='Enter one ingredient per line';addRecipeEditorSourceLink(url);
 for(const [field,title]of [[ingredients,'Ingredients'],[instructions,'Steps'],[notes,'Recipe notes']])collapseRecipeEditorField(field,title);
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');d.panel.append(error);
 const owner='viewer-recipe:'+meal.id+':'+(crypto.randomUUID?.()||Date.now()),read=()=>({ingredients:ingredients.value,instructions:instructions.value,url:url.value,notes:notes.value}),initial=JSON.stringify(read());
 const close=()=>{mealPersistence.cancelOwner(owner);d.close();view.contentEdit=null;requestRecipeImportResume()};
 view.contentEdit={close};d.overlay.dataset.viewerRecipeDraft='';const keys=d.overlay.onkeydown;d.overlay.onkeydown=e=>{e.stopPropagation();if(e.key==='Escape'){e.preventDefault();close()}else keys(e)};d.overlay.onclick=e=>{if(e.target===d.overlay)close()};
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Save recipe');setIconButton(cancel,'cancel','Cancel');cancel.onclick=close;actions.append(save,cancel);d.panel.append(actions);
 let saving=false;save.onclick=()=>{if(saving)return;saving=true;error.textContent='';try{
  if(recipeViewer!==view)throw Error('Reopen this recipe before saving.');
  const current=meals.find(m=>String(m.id)===String(meal.id));if(!current)throw Error('This recipe no longer exists.');
  const draft=read(),patch={};if(draft.ingredients!==(original.ingredients||[]).join('\n'))patch.ingredients=draft.ingredients.split('\n').map(s=>s.trim()).filter(Boolean);
  if(draft.instructions!==instructionEditorText(original.instructions))patch.instructions=instructionBlocks(draft.instructions);
  if(draft.notes!==String(original.notes||''))patch.notes=draft.notes;
  if(draft.url!==recipeDisplaySourceUrl(original)){const value=draft.url.trim();patch.recipeSourceHidden=!value;if(value){patch.url=value;patch.originalRecipeUrl=value}}
  if(patch.ingredients||patch.instructions)if(Array.isArray(current.ingredientStepLinks))patch.ingredientStepLinks=validRecipeIngredientLinks({...current,...patch});
  const ids=sharedRecipeMembers(current).map(m=>String(m.id));
  applyRecipeBulk([String(current.id)],{}, {render:false,viewerEdit:{sourceId:String(current.id),fields:patch,owner}});
  for(const tab of view.tabCache.values())if(ids.includes(tab.mealId)){const record=meals.find(m=>String(m.id)===tab.mealId);tab.previewProgress=compatiblePreviewProgress(tab.previewProgress,tab.recipeContent,record);tab.recipeContent={ingredients:record.ingredients,instructions:record.instructions}}
  close();view.contentChanged=true;view.restoreTabScroll=true;view.syncGeometryHold=true;renderRecipeViewer();view.cover.querySelector('[aria-label="Edit Recipe"]')?.focus({preventScroll:true});
 }catch(e){error.textContent='Recipe could not be saved: '+e.message+' Your draft is still open.'}finally{saving=false}};
 d.overlay.mealRecoveryDraft={ownerId:owner,kind:'viewer-recipe-editor',capture:()=>({recipeId:String(meal.id),fields:read()}),dirty:()=>JSON.stringify(read())!==initial,save:()=>save.onclick(),discard:close};fitOneTimeMealViewport(d.overlay,d.panel);ingredients.focus({preventScroll:true});
}
function applyViewerRecipeMutation(edit,before){
 const source=meals.find(m=>String(m.id)===edit.sourceId);if(!source)throw Error('This recipe no longer exists.');
 const allowed=new Set(['ingredients','instructions','url','originalRecipeUrl','recipeSourceHidden','notes','ingredientStepLinks']);if(Object.keys(edit.fields).some(key=>!allowed.has(key)))throw Error('Unsupported recipe content field.');
 if(edit.fields.ingredients){
  const selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');let changed=false;
  for(const member of sharedRecipeMembers(source)){
   const key=String(member.id),selected=selections[key];if(!Array.isArray(selected))continue;
   const next=edit.fields.ingredients,remap=line=>{if(next.some(value=>ingredientKey(value)===ingredientKey(line)))return line;const quantity=groceryQuantityParts(line),oldMatches=(member.ingredients||[]).filter(value=>groceryQuantityParts(value)?.key===quantity?.key),matches=quantity?next.filter(value=>groceryQuantityParts(value)?.key===quantity.key):[];return quantity&&oldMatches.length===1&&matches.length===1?matches[0]:line};
   const revised=selected.map(remap);if(JSON.stringify(selected)!==JSON.stringify(revised)){(before.bulkRecipeUndoSelections||={})[key]=[...selected];selections[key]=revised;changed=true}
  }
  if(changed)localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selections));
 }
 assignSharedRecipeFields(source,edit.fields);
}
function compatiblePreviewProgress(progress,oldMeal,meal){
 const next=JSON.parse(JSON.stringify(progress)),items=cookingItemTokens(meal);
 for(const kind of ['ingredients','steps']){const changed=JSON.stringify(oldMeal?.[kind==='steps'?'instructions':kind])!==JSON.stringify(meal[kind==='steps'?'instructions':kind]),counts=new Map();for(const item of items[kind])if(item.token){const base=item.token.replace(/#\d+$/,'');counts.set(base,(counts.get(base)||0)+1)}const allowed=new Set(items[kind].filter(i=>i.token&&(!changed||counts.get(i.token.replace(/#\d+$/,''))===1)).map(i=>i.token));next[kind]=(next[kind]||[]).filter(t=>allowed.has(t));if(kind==='ingredients'){if(next.autoIngredients)next.autoIngredients=next.autoIngredients.filter(t=>allowed.has(t));if(next.ingredientOverrides)next.ingredientOverrides=Object.fromEntries(Object.entries(next.ingredientOverrides).filter(([t])=>allowed.has(t)))}}
 if((next.autoIngredients||next.ingredientOverrides)&&(JSON.stringify(oldMeal?.ingredients)!==JSON.stringify(meal.ingredients)||JSON.stringify(oldMeal?.instructions)!==JSON.stringify(meal.instructions)))updateAutomaticCookingIngredients(next,meal);return next;
}
function returnToEditedRecipe(){
 const saved=recipeEditorReturn;if(!saved)return false;recipeEditorReturn=null;
 const anchor=saved.viewerTabs?.anchor,meal=meals.find(m=>String(m.id)===String(anchor?.mealId||saved.mealId));
 if(!meal){if(window.history.state?.mealRotationRecipeViewer){const state={...window.history.state};delete state.mealRotationRecipeViewer;window.history.replaceState(state,'')}return true}
 const context=definiteRecipeContext(anchor?.context||saved.context);
 openRecipeViewer(meal,context,false,saved.viewerTabs,saved.navigationOrigin);const view=recipeViewer;view.scroll=saved.appScroll;
 if(!saved.viewerTabs){view.previewProgress=compatiblePreviewProgress(saved.previewProgress,saved.recipeContent,meal);view.previewScale=saved.previewScale;renderRecipeViewer();view.cover.scrollTop=saved.scroll;[...view.content.querySelectorAll('.recipe-pane')].forEach((p,i)=>p.scrollTop=saved.panes[i]||0)}
 window.history.replaceState({...window.history.state,mealRotationRecipeViewer:{mealId:view.anchorTab.mealId,context:view.anchorTab.context}},'');return true;
}

// Move the existing controls intact; collapse never re-renders or resets a draft.
function organizeMealEditor(){
 const root=document.querySelector('#editor .editor'),actions=root.querySelector(':scope>.actions'),fields=document.createElement('div'),sections=document.createElement('div'),content={};
 fields.className='meal-editor-fields';sections.className='meal-editor-sections';
 const meal=meals.find(m=>m.id===editId),isNew=newRecipeDraftId===editId&&!scheduledMealEditor?.current;
 for(const [key,title]of [['serve','Serve with'],['recipe','Recipe'],['notes','Notes & Reminders']]){
  const group=makeSettingsGroup(key,title);delete group.details.dataset.settingsGroup;group.details.dataset.editorSection=key;group.details.classList.add('meal-editor-section');
  const summary=document.createElement('span');summary.className='meal-editor-summary';summary.dataset.editorSummary=key;
  if(key==='serve'){const names=normalizeServeWith(meal.serveWith);summary.textContent=names.length===1?names[0]:names.length?names.length+' selected':''}
  if(key==='linked'){const ids=new Set((meal.linkedMealIds||[]).map(String));const count=meals.filter(m=>ids.has(String(m.id))).length;summary.textContent=count?count+' linked':''}
  if(key==='recipe')summary.textContent=(meal.ingredients||[]).some(x=>String(x).trim())||instructionBlocks(meal.instructions).some(x=>x.text?.trim())||String(meal.url||'').trim()?'Added':'';
  if(key==='notes')summary.textContent=String(meal.notes||'').trim()||meal.needsTweaking||recipeMakeAheadTasks(meal).length?'Added':'';
  group.details.querySelector('summary').insertBefore(summary,group.details.querySelector('.settings-chevron'));
  group.details.open=false;
  content[key]=group.content;sections.append(group.details);
 }
 const rotation=$('rotation').closest('label');rotation.querySelector('span').textContent='Add to rotation';rotation.classList.add('meal-card-rotation-control');$('categoryRows').after(rotation);root.querySelector('label').htmlFor='name';$('categoryRows').previousElementSibling.htmlFor='cat';$('categoryRows').previousElementSibling.textContent='Meal Groups';
 for(const [id,title]of [['prep','Prep'],['totaltime','Total'],['marinate','Marinate']])document.querySelector('label[for="'+id+'"]').textContent=title;
 const buttons=$('serveWith').parentElement;content.serve.append($('serveWith'));const linkedBody=document.createElement('div');linkedBody.id='mealCardLinkedBody';linkedBody.className='settings-group-content';linkedBody.append($('editLinkedMeals'));root.append(linkedBody);buttons.remove();
 const url=$('url'),urlLabel=url.previousElementSibling;urlLabel.textContent='Recipe URL';urlLabel.htmlFor='url';content.recipe.append($('editorIngredientsSection'),$('editorInstructionsSection'),$('recipeIngredientLinks'),$('editorNeedsTweaking'),urlLabel,url);addRecipeEditorSourceLink(url);
 content.notes.append($('recipeMakeAhead'),$('editorNotesSection'));
 for(const child of [...root.children])if(child!==actions)fields.append(child);fields.append(sections);actions.before(fields);installMealEditorLayout(root,fields);
}
// The toolbar belongs to this bounded editor, never to the surrounding page.
function installMealEditorLayout(root,fields){
 const events=new AbortController(),viewport=window.visualViewport,vk=navigator.virtualKeyboard;let frame=0,baseline=Math.max(viewport?.height||0,innerHeight,document.documentElement.clientHeight),width=innerWidth,keyboardOpen=false;
 const fit=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
  if(!root.isConnected)return;const height=viewport?.height||innerHeight,offset=viewport?.offsetTop||0;
  if(Math.abs(innerWidth-width)>80){baseline=Math.max(height,innerHeight,document.documentElement.clientHeight);width=innerWidth;keyboardOpen=false}else baseline=Math.max(baseline,height,innerHeight,document.documentElement.clientHeight);
  const active=document.activeElement,editing=fields.contains(active)&&active.matches('textarea,input:not([type=checkbox]):not([type=radio]):not([type=hidden]):not([type=file]),[contenteditable=true]');
  const reduced=(viewport?.scale||1)===1&&baseline-height>=Math.max(120,baseline*.2);
  keyboardOpen=(vk?.boundingRect?.height||0)>0||reduced&&(editing||keyboardOpen);root.classList.toggle('meal-editor-keyboard-open',keyboardOpen);
  const top=root.closest('[role=dialog]')?130:Math.max(0,root.getBoundingClientRect().top-offset)+16;root.style.setProperty('--meal-editor-height',Math.max(140,height-top)+'px');
  if(fields.contains(active)){const field=active.getBoundingClientRect(),box=fields.getBoundingClientRect();if(field.height>box.height-16)fields.scrollTop+=field.top-box.top-8;else if(field.bottom>box.bottom-8)fields.scrollTop+=field.bottom-box.bottom+8;else if(field.top<box.top+8)fields.scrollTop-=box.top+8-field.top}
 })};
 viewport?.addEventListener('resize',fit,{signal:events.signal});viewport?.addEventListener('scroll',fit,{signal:events.signal});vk?.addEventListener('geometrychange',fit,{signal:events.signal});window.addEventListener('resize',fit,{signal:events.signal});fields.addEventListener('focusin',fit,{signal:events.signal});window.addEventListener('scroll',fit,{passive:true,signal:events.signal});
 const resize=new ResizeObserver(fit);resize.observe(root);const observer=new MutationObserver(()=>{if(!root.isConnected){events.abort();cancelAnimationFrame(frame);resize.disconnect();observer.disconnect()}});observer.observe(document.body,{childList:true,subtree:true});fit();
}
function revealMealEditorField(field){
 if(!field)return;field.revealCardField?.();for(let parent=field;parent&&parent.id!=='editor';parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;
 (field.tagName==='DETAILS'?field.querySelector('summary'):field)?.focus({preventScroll:true});field.scrollIntoView({block:'nearest',behavior:'instant'});
}

function buildRecipeEditorSections(meal){
 const field=$('recipeInstructions'),label=field.previousElementSibling,hint=field.nextElementSibling;
 const ingredients=mealEditorSubsection('ingredients','Ingredients','editorIngredientsSection',meal).details;label.before(ingredients);ingredients.before($('rotation').closest('label'));ingredients.querySelector('.settings-group-content').append($('ingredientsClosed'),$('ingredientsPanel'));$('ingredientsClosed').classList.add('hidden');$('hideIngredients').classList.add('hidden');
 const instructions=mealEditorSubsection('instructions','Steps','editorInstructionsSection',meal).details;label.before(instructions);
 const closed=document.createElement('div');closed.id='instructionsClosed';const show=document.createElement('button');show.id='toggleInstructions';show.className='smallbtn';show.type='button';show.textContent='Steps';closed.append(show);
 const panel=document.createElement('div');panel.id='instructionsPanel';panel.className='ingredients-panel';const tools=document.createElement('div');tools.className='ingredient-toolrow';const hide=document.createElement('button');hide.id='hideInstructions';hide.type='button';hide.className='smallbtn';hide.textContent='Hide steps';tools.append(hide);
 for(const [id,source,title] of [['instructionPhotoButton','ingredientPhotoButton','Choose cooking instructions photo from gallery'],['instructionCameraButton','ingredientCameraButton','Take cooking instructions photo']]){const button=document.createElement('button');button.id=id;button.type='button';button.className='ingredient-tool';button.title=title;button.setAttribute('aria-label',title);button.innerHTML=$(source).innerHTML;tools.append(button)}
 field.setAttribute('aria-label','Steps');label.remove();panel.append(tools,field,hint);
 for(const [id,camera] of [['instructionGalleryInput',false],['instructionCameraInput',true]]){const input=document.createElement('input');input.id=id;input.type='file';input.accept='image/*';input.className='hidden';if(camera)input.setAttribute('capture','environment');panel.append(input)}
 instructions.querySelector('.settings-group-content').append(closed,panel);closed.classList.add('hidden');hide.classList.add('hidden');const links=$('recipeIngredientLinks');links.replaceWith(mealEditorSubsection('links','Link Steps','recipeIngredientLinks',meal).details);buildRecipeNotesSection(meal);
 for(const [section,row]of [[ingredients,$('ingredientsPanel').querySelector('.ingredient-toolrow')],[instructions,tools]]){
  const summary=section.querySelector('summary');summary.append(row);row.style.cssText='display:flex;gap:4px;margin:0 0 0 auto;flex-wrap:nowrap';
  for(const button of row.querySelectorAll('.ingredient-tool')){button.style.cssText='width:30px;height:30px;flex:0 0 30px;padding:5px';button.querySelector('svg').style.cssText='width:18px;height:18px';button.addEventListener('click',event=>event.stopPropagation())}
 }
 const display=open=>{instructions.open=open;panel.classList.toggle('hidden',!open)};show.onclick=()=>display(true);hide.onclick=()=>display(false);instructions.addEventListener('toggle',()=>display(instructions.open));display(false);
}
async function importInstructionsFromPhoto(file,mealId){
 const field=$('recipeInstructions');if(!file||!file.type.startsWith('image/')||!field)return;
 const progress=showImportProgressDialog('Reading cooking instructions from photo…');let timer;
 try{
  const result=await Promise.race([(async()=>{if(await ingredientPhotoIsBlank(file))return {blank:true};if(progress.signal.aborted)return {cancelled:true};return {text:await recognizeIngredientPhoto(file,progress.signal)}})(),progress.cancelled,new Promise(resolve=>{timer=setTimeout(()=>resolve({timedOut:true}),60000)})]);
  if(result.timedOut)progress.abort();progress.close();if(result.cancelled||editId!==mealId||!field.isConnected)return;
  if(result.timedOut||result.blank||!String(result.text||'').trim()){await showAppMessage(result.timedOut?'The photo could not be read in time. Try a clearer photo or type the instructions.':'No readable cooking instructions were found in the photo.');return}
  const raw=String(result.text).trim(),sections=recipeTextSections(raw),blocks=sections.instructions.some(b=>b.type==='step')?sections.instructions:cleanupRecipeInstructions(raw).instructions.map(cleanInstructionBlock);
  const reviewed=await reviewPhotoIngredients(instructionEditorText(blocks),raw,'instructions');if(reviewed===null||editId!==mealId||!field.isConnected)return;
  const clean=importedInstructionBlocks(reviewed).map(cleanInstructionBlock);if(!clean.some(b=>b.type==='step')){await showAppMessage('No cooking steps were provided. Your existing instructions have been kept.');return}
  if(field.value.trim()&&!await appDialog('Replace the existing cooking instructions with the reviewed text?',null,'yesno'))return;
  if(editId!==mealId||!field.isConnected)return;field.recipeImportReferences=mergeRecipeImportReferences(sections.recipeImportReferences||[],cleanupRecipeInstructions(raw).related);field.value=instructionEditorText(clean);field.dispatchEvent(new Event('change',{bubbles:true}));
 }catch(e){progress.close();if(!progress.signal.aborted&&editId===mealId)await showAppMessage('Cooking instructions could not be read from this photo. Your existing draft has been kept.')}finally{clearTimeout(timer);progress.close()}
}
function installInstructionPhotoControls(meal){
 for(const [button,input] of [['instructionPhotoButton','instructionGalleryInput'],['instructionCameraButton','instructionCameraInput']]){$(button).onclick=()=>$(input).click();$(input).onchange=e=>{const file=e.target.files?.[0];e.target.value='';if(file)importInstructionsFromPhoto(file,meal.id)}}
}

let addingGroupRecipe=false,newRecipeDraftId=null;
function addRecipeToGroup(category){
 // Keep the whole create/open sequence single-flight, including detached old + controls.
 if(addingGroupRecipe||(category!==''&&!cats.includes(category))||!prepareRecipeCreation())return;
 addingGroupRecipe=true;
 try{
  if(tutorialStage==='2')setTutorialStage('editing');snapshot();
  const meal={id:id++,cat:category,name:'',rotation:false,groceryDefaultAll:true,prep:'',cook:'',total:'',url:'',ingredients:[]};
  meals.push(meal);newRecipeDraftId=meal.id;
  masterExpansionInitialized=true;masterExpandedCategories.add(category);
  if(category){setMasterRecipeSectionOpen(category,false,true);setMasterRecipeSectionOpen(category,true,false)}
  openEditor(meal.id,true);
 }finally{addingGroupRecipe=false}
}
let editorCategoryBaseline=null,editorDraftCategories=null;
let mealEditorReturnScroll=null,mealEditorReturnView=null;
// Capture the entry point before the inline editor switches to Meal Groups.
// Section preferences are part of that context, not a side effect of editing.
function captureMealEditorOrigin(){
 return {...appViewSnapshot(),activeCategory:active,expandedCategories:[...masterExpandedCategories],expansionInitialized:masterExpansionInitialized,sections:[...masterSectionExpansion].map(([cat,value])=>[cat,{...value}]),scroll:window.scrollY};
}
function restoreMealEditorScroll(){
 dismissEditorHistory();stopMealEditorPositioning();
 const position=mealEditorReturnScroll,origin=mealEditorReturnView;
 mealEditorReturnScroll=null;mealEditorReturnView=null;
 if(origin){
  if(origin.planId!==activePlanId&&mealPlans.some(plan=>plan.id===origin.planId))loadMealPlan(origin.planId,false);
  showTop=origin.view!=='groups';groceryTabActive=origin.view==='grocery';allMealsActive=origin.view==='all';setMasterCategoriesView(!showTop);
  if(cats.includes(origin.activeCategory))active=origin.activeCategory;
  masterExpansionInitialized=origin.expansionInitialized;masterExpandedCategories.clear();origin.expandedCategories.filter(cat=>cat===''||cats.includes(cat)).forEach(cat=>masterExpandedCategories.add(cat));
  if(origin.sections){masterSectionExpansion.clear();origin.sections.forEach(([cat,value])=>masterSectionExpansion.set(cat,{...value}));saveMasterSectionExpansion()}
 }
 // Render only after restoring the origin, avoiding a flash of the editor's host page.
 render();
 if(returnToEditedRecipe())return;
 origin?.resumeDialog?.();
 if(position===null)return;
 window.scrollTo({top:position,behavior:'instant'});
 requestAnimationFrame(()=>requestAnimationFrame(()=>{
  // An outside tap may intentionally navigate elsewhere after closing the editor.
  if(origin&&(activePlanId!==origin.planId||appViewSnapshot().view!==origin.view))return;
  if(editId===null)window.scrollTo({top:position,behavior:'instant'});
 }));
}
function rollbackEditorCategories(){if(!editorCategoryBaseline)return;if(newRecipeDraftId===editorCategoryBaseline.newMealId)newRecipeDraftId=null;meals=JSON.parse(editorCategoryBaseline.meals);id=editorCategoryBaseline.id;if(editorCategoryBaseline.labelCatalog!==undefined){recipeLabelCatalog=JSON.parse(editorCategoryBaseline.labelCatalog);weekdayRecipeFilters=JSON.parse(editorCategoryBaseline.labelFilters);mealPlans=JSON.parse(editorCategoryBaseline.labelPlans);const activePlan=mealPlans.find(p=>p.id===activePlanId);if(activePlan)activePlan.weekdayRecipeFilters=JSON.parse(editorCategoryBaseline.labelFilters);saveRecipeLabelCatalog();saveWeekdayRecipeFilters();}try{localStorage.setItem('mealRotationSelectedIngredientsV1',editorCategoryBaseline.selections)}catch(e){}editorCategoryBaseline=null;editorDraftCategories=null;persist()}
let stopMealEditorPositioning=()=>{};
function mealEditorRow(){
 const editing=document.querySelector('#editor .meal-card-edit-mode');if(editing&&editing.dataset.mealId===String(editId))return editing;
 const meal=meals.find(item=>String(item.id)===String(editId));
 if(!meal)return null;
 const card=[...document.querySelectorAll('#list .master-category-card')].find(el=>el.dataset.category===meal.cat);
 return [...(card||$('list')).querySelectorAll('[data-meal-id]')].find(el=>el.dataset.mealId===String(meal.id))||null;
}
function positionMealEditor(focusNewMeal=false){
 stopMealEditorPositioning();
 const targetId=editId;let frame=0;const timers=[];
 function align(){
  if(editId!==targetId)return;
  const row=mealEditorRow();if(!row)return;
  // Reserve the space occupied by this group's sticky heading, including
  // visual-viewport offsets while a mobile keyboard is opening or closing.
  const viewportTop=window.visualViewport?.offsetTop||0;
  const header=row.closest('.master-category-card')?.querySelector('.master-category-header');
  const headerStyle=header&&getComputedStyle(header);
  const headerHeight=headerStyle&&headerStyle.position==='sticky'?header.getBoundingClientRect().height+Math.max(0,parseFloat(headerStyle.top)||0):0;
  const top=window.scrollY+row.getBoundingClientRect().top-viewportTop-headerHeight-24;
  window.scrollTo({top:Math.max(0,top),behavior:'instant'});
 }
 function schedule(){cancelAnimationFrame(frame);frame=requestAnimationFrame(align)}
 const viewport=window.visualViewport;
 viewport?.addEventListener('resize',schedule);
 viewport?.addEventListener('scroll',schedule);
 window.addEventListener('resize',schedule);
 stopMealEditorPositioning=()=>{cancelAnimationFrame(frame);timers.forEach(clearTimeout);viewport?.removeEventListener('resize',schedule);viewport?.removeEventListener('scroll',schedule);window.removeEventListener('resize',schedule)};
 requestAnimationFrame(()=>{
  if(editId!==targetId)return;
  const row=mealEditorRow();
  document.querySelectorAll('.meal-editor-located').forEach(el=>el.classList.remove('meal-editor-located'));
  if(row){row.classList.add('meal-editor-located');setTimeout(()=>row.classList.remove('meal-editor-located'),1800)}
  if(focusNewMeal){if(!scheduledMealEditor?.current&&$('name')?.revealCardField)$('name').revealCardField();else $('name')?.focus({preventScroll:true})}
  schedule();
 });
 timers.push(setTimeout(schedule,250),setTimeout(schedule,500),setTimeout(()=>stopMealEditorPositioning(),800));
}
function openEditor(n,focusNewMeal=false,navigationOrigin=null){
 if(editId===null){mealEditorReturnView=navigationOrigin||captureMealEditorOrigin();mealEditorReturnScroll=mealEditorReturnView.scroll}
 stopMealEditorPositioning();
 rollbackEditorCategories();
 const selectedMeal=meals.find(item=>String(item.id)===String(n));if(!selectedMeal)return;
 // Every entry point reveals the recipe's own group and row before attaching
 // the one shared editor. Recipe-viewer return state remains separate.
 editId=null;setMasterCategoriesView(true);showTop=false;groceryTabActive=false;allMealsActive=false;
 masterExpansionInitialized=true;masterExpandedCategories.add(selectedMeal.cat);
 if(selectedMeal.cat)setMasterRecipeSectionOpen(selectedMeal.cat,!!selectedMeal.rotation,true);
 active=selectedMeal.cat;menuCat=null;render();
 editorCategoryBaseline={newMealId:newRecipeDraftId===selectedMeal.id?selectedMeal.id:null,meals:JSON.stringify(meals.filter(meal=>meal.id!==newRecipeDraftId)),id,selections:localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}',labelCatalog:JSON.stringify(recipeLabelCatalog),labelFilters:JSON.stringify(weekdayRecipeFilters),labelPlans:JSON.stringify(mealPlans)};
 editId=selectedMeal.id;
 editorDraftCategories=[...new Set([selectedMeal.cat,...(selectedMeal.linkGroup?meals.filter(x=>x.linkGroup===selectedMeal.linkGroup):[selectedMeal]).map(x=>x.cat)].filter(Boolean))];
 if(mealEditorReturnView?.view==='groups'&&!recipeEditorReturn&&!window.history.state?.mealRotationEditor)window.history.pushState({...window.history.state,mealRotationView:{view:'groups',planId:activePlanId},mealRotationEditor:String(editId)},'');
 renderEditor();placeEditorInline();positionMealEditor(focusNewMeal);
}
function renderEditor(){let m=meals.find(x=>x.id===editId);if(!m){$('editor').innerHTML='';return}$('editor').innerHTML=`<div class="editor"><label>Meal name</label><input id="name" type="text" value="${esc(m.name)}"><label>Group</label><div id="categoryRows"></div><div class="grid time-editor-grid"><div class="time-prep"><label for="prep">Prep time</label><input id="prep" type="text" inputmode="decimal" value="${esc(prettyTimeInput(m.prep))}"></div><div class="time-total"><label for="totaltime">Total time</label><input id="totaltime" type="text" inputmode="decimal" value="${esc(prettyTimeInput(m.total!==undefined&&m.total!==''?m.total:(m.prep!==''||m.cook!==''?(Number(m.prep)||0)+(Number(m.cook)||0):'')))}"></div><div class="time-marinate"><label for="marinate">Marinate time</label><input id="marinate" type="text" inputmode="decimal" value="${esc(m.marinate??'')}"></div></div><div class="time-keyboard-tools hidden"><button id="timeKeyboardMode" type="button" title="Switch to letter keyboard for time units" aria-label="Switch to letter keyboard for time units">ABC</button></div><div class="recipe-related-buttons"><button id="serveWith" type="button" class="smallbtn">Serve with</button><button id="editLinkedMeals" type="button" class="smallbtn">↗ Linked Meals</button></div><label>Recipe URL</label><input id="url" type="text" placeholder="https://" value="${esc(m.url)}"><label for="recipeInstructions">Steps</label><textarea id="recipeInstructions" class="ingredients-input" placeholder="One step per line. Use ## for section headings.">${esc(instructionEditorText(m.instructions))}</textarea><div class="muted">One step per line; use ## Heading to start a section.</div><details id="recipeIngredientLinks"><summary>Step links</summary></details><label for="recipeNotes">Notes</label><textarea id="recipeNotes" class="ingredients-input">${esc(m.notes||'')}</textarea><div id="ingredientsClosed"><button id="toggleIngredients" class="smallbtn" type="button">Ingredients</button></div><div id="ingredientsPanel" class="ingredients-panel hidden"><div class="ingredient-toolrow"><button id="hideIngredients" class="smallbtn" type="button">Hide ingredients</button><button id="ingredientLinkButton" class="ingredient-tool" type="button" title="Import ingredients from website link" aria-label="Import ingredients from website link"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.1 0l3-3a5 5 0 0 0-7.1-7.1l-1.7 1.7M14 11a5 5 0 0 0-7.1 0l-3 3a5 5 0 0 0 7.1 7.1l1.7-1.7"/></svg></button><button id="ingredientPhotoButton" class="ingredient-tool" type="button" title="Choose ingredient photo from gallery" aria-label="Choose ingredient photo from gallery"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg></button><button id="ingredientCameraButton" class="ingredient-tool" type="button" title="Take ingredient photo" aria-label="Take ingredient photo"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h4l2-3h4l2 3h4a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z"/><circle cx="12" cy="13" r="4"/></svg></button></div><label id="ingredientsLabel">Enter one ingredient per line</label><textarea id="ingredients" class="ingredients-input" placeholder="Enter one ingredient per line">${esc((m.ingredients||[]).map(removeIngredientListMarker).join('\n'))}</textarea><input id="ingredientGalleryInput" type="file" accept="image/*" class="hidden"><input id="ingredientCameraInput" type="file" accept="image/*" capture="environment" class="hidden"></div><label class="meal-checkbox-option"><input id="rotation" type="checkbox" ${m.rotation||newRecipeDraftId===m.id?'checked':''}><span>Add to rotation</span></label><div class="actions"><button id="save" type="button" title="Save" aria-label="Save"><svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l4 4L19 6"/></svg></button><button id="delete" type="button" title="Delete" aria-label="Delete"><svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2m3 0-1 15H6L5 6m5 4v7m4-7v7"/></svg></button><button id="cancel" type="button" title="Cancel" aria-label="Cancel"><svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></button></div></div>`;buildRecipeEditorSections(m);buildRecipeTweakingEditor(m);buildMakeAheadEditor(m);organizeMealEditor();function categoryMembers(){return m.linkGroup?meals.filter(x=>x.linkGroup===m.linkGroup):[m]}
let editorMembershipDraft=categoryMembers().map(record=>({id:String(record.id),cat:record.cat}));
const pendingEditorGroups=[];
const editorGroupNames=()=>[...cats,...pendingEditorGroups];
function draftGroupNameField(panel){
 const input=stage2FormField(panel,'New group name',document.createElement('input'));input.type='text';
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');panel.append(error);
 return {input,error};
}
if(!editorDraftCategories)editorDraftCategories=[...new Set(categoryMembers().map(x=>x.cat).filter(Boolean))];
function renderCategoryRows(){
 const holder=$('categoryRows');if(!holder)return;holder.replaceChildren();
 const primary=editorMembershipDraft.find(item=>String(item.id)===String(m.id));
 if(!primary)return;
 const selectedGroups=()=>[...new Set(editorMembershipDraft.filter(item=>!item.removed&&item.cat).map(item=>item.cat))];
 const select=document.createElement('select');select.id='cat';select.hidden=true;select.tabIndex=-1;
 const current=selectedGroups();$('rotation').disabled=!current.length&&!scheduledMealEditor?.oneTime;const primaryOption=document.createElement('option');primaryOption.value=primary.cat||'';primaryOption.textContent=primary.cat||'No group';select.append(primaryOption);select.value=primary.cat||'';holder.append(select);
 const display=document.createElement('span');display.className='meal-group-assigned-list';display.textContent=current.length?(current.join(', ')):'Unassigned';if(!current.length)display.classList.add('is-unassigned');const picker=document.createElement('button');picker.type='button';picker.className='iconbtn meal-group-picker-button';setIconButton(picker,'add','Edit meal groups');picker.setAttribute('aria-haspopup','dialog');
 picker.onclick=()=>{
  const d=recipeBulkDialog(m.cat===''&&newRecipeDraftId===m.id?'Choose a group for your recipe':'Select Meal Group',()=>picker),list=document.createElement('div');list.className='meal-group-picker-options';list.setAttribute('role','group');list.setAttribute('aria-label','Meal Groups');
  const selected=new Set(selectedGroups());
  for(const cat of editorGroupNames()){const label=document.createElement('label'),check=document.createElement('input'),text=document.createElement('span');check.type='checkbox';check.value=cat;check.checked=selected.has(cat);text.textContent=cat;label.append(check,text);check.onchange=()=>{if(check.checked)selected.add(cat);else selected.delete(cat)};list.append(label)}
  const clear=document.createElement('button');clear.type='button';clear.className='smallbtn';clear.textContent='Remove all group assignments';clear.onclick=()=>{selected.clear();list.querySelectorAll('input').forEach(input=>input.checked=false)};d.panel.append(list,clear);const newGroup=scheduledMealEditor?null:draftGroupNameField(d.panel);
  const actions=document.createElement('div');actions.style.cssText='display:flex;align-items:center;justify-content:center;gap:48px;margin:12px auto 0';
  const apply=document.createElement('button');apply.type='button';apply.className='iconbtn';setIconButton(apply,'save','Apply selected groups');apply.style.cssText+=';width:44px;height:44px';
  apply.onclick=()=>{
   if(newGroup?.input.value.trim()){
    try{const name=validateNewMealGroupName(newGroup.input.value,editorGroupNames());pendingEditorGroups.push(name);selected.add(name)}
    catch(error){newGroup.error.textContent=error.message;newGroup.input.focus();return}
   }
   const chosen=editorGroupNames().filter(cat=>selected.has(cat)),existing=editorMembershipDraft.filter(item=>item!==primary&&!item.removed),oldPrimary=primary.cat;
   const primaryCat=selected.has(oldPrimary)?oldPrimary:(chosen[0]||'');primary.cat=primaryCat;primary.removed=false;
   const remaining=new Set(chosen.filter(cat=>cat!==primaryCat));
   for(const item of existing){if(remaining.has(item.cat)){remaining.delete(item.cat)}else{item.cat='';item.removed=true}}
   for(const cat of remaining)editorMembershipDraft.push({id:null,cat});
   editorDraftCategories=chosen;d.close();renderCategoryRows();
  };
  const cancel=document.createElement('button');cancel.type='button';cancel.className='iconbtn';setIconButton(cancel,'cancel','Close without changes');cancel.style.cssText+=';width:44px;height:44px';cancel.onclick=d.close;
  actions.append(apply,cancel);d.panel.append(actions);cancel.focus({preventScroll:true});
 };const heading=holder.previousElementSibling;if(heading?.tagName==='LABEL'){heading.classList.add('meal-group-editor-heading');heading.querySelectorAll('.meal-group-assigned-list,.meal-group-picker-button').forEach(el=>el.remove());heading.append(display,picker)}else holder.append(display,picker);
}

['save','delete','cancel'].forEach(k=>{const b=$(k);b.style.cssText='border:0;background:transparent;color:inherit;min-height:44px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer'});renderCategoryRows();
// Prefer the numeric/decimal keyboard, while providing a reliable ABC/123
// switch for phones whose numeric keyboard doesn't have a letters key.
const timeFields=['prep','totaltime','marinate'].map($);
const keyboardButton=$('timeKeyboardMode');
const keyboardTools=keyboardButton.parentElement;
let activeTimeField=timeFields[0];
let alphabetKeyboard=false;
timeFields.forEach(field=>field.addEventListener('focus',()=>{
  activeTimeField=field;
  keyboardTools.classList.remove('hidden');
}));
keyboardButton.onclick=()=>{
  alphabetKeyboard=!alphabetKeyboard;
  timeFields.forEach(field=>field.setAttribute('inputmode',alphabetKeyboard?'text':'decimal'));
  keyboardButton.textContent=alphabetKeyboard?'123':'ABC';
  const label=alphabetKeyboard?'Switch to number keyboard':'Switch to letter keyboard for time units';
  keyboardButton.title=label;
  keyboardButton.setAttribute('aria-label',label);
  // Re-focus to request the updated keyboard layout on Android browsers.
  if(activeTimeField.isConnected){activeTimeField.blur();if(activeTimeField.revealCardField)activeTimeField.revealCardField();else activeTimeField.focus();}
};
let serveWithDraft=normalizeServeWith(m.serveWith);
const serveButton=$('serveWith');serveButton.hidden=true;serveButton.readDraft=()=>[...serveWithDraft];
const serveBody=serveButton.parentElement,chips=document.createElement('div'),suggestions=document.createElement('div'),customRow=document.createElement('div'),custom=document.createElement('input');
chips.className='meal-editor-chips';suggestions.className='meal-editor-suggestions';customRow.className='meal-editor-custom';custom.type='text';custom.placeholder='Add custom suggestion...';custom.setAttribute('aria-label','Custom Serve with suggestion');
const suggestionTitle=document.createElement('div');suggestionTitle.className='muted';suggestionTitle.textContent='Choose which types of sides to automatically rotate in with this meal.';suggestionTitle.style.cssText='font-size:12px;line-height:1.4;margin:6px 0 8px';
const options=normalizeServeWith(['Rice','Potatoes','Pasta','Vegetables','Bread',...serveWithDraft]);
function updateServeWith(){
 chips.replaceChildren();suggestions.replaceChildren();
 for(const name of serveWithDraft){const remove=document.createElement('button');remove.type='button';remove.className='meal-editor-chip';remove.textContent=name+' ×';remove.setAttribute('aria-label','Remove Serve with '+name);remove.onclick=()=>{serveWithDraft=serveWithDraft.filter(value=>serveWithWords(value)!==serveWithWords(name));updateServeWith()};chips.append(remove)}
 for(const name of options.filter(name=>!serveWithDraft.some(value=>serveWithWords(value)===serveWithWords(name)))){const add=document.createElement('button');add.type='button';add.className='meal-editor-chip';add.textContent=name;add.onclick=()=>{serveWithDraft=normalizeServeWith([...serveWithDraft,name]);updateServeWith()};suggestions.append(add)}
 document.querySelector('#editor .editor')?.refreshIndicators?.();
}
const addCustom=document.createElement('button');addCustom.type='button';addCustom.className='meal-editor-inline-icon';setIconButton(addCustom,'add','Add custom Serve with suggestion');
function addServeCustom(){const value=custom.value.trim();if(!serveWithWords(value))return;if(!serveWithDraft.some(name=>serveWithWords(name)===serveWithWords(value)))serveWithDraft.push(value);if(!options.some(name=>serveWithWords(name)===serveWithWords(value)))options.push(value);custom.value='';updateServeWith()}
addCustom.onclick=addServeCustom;custom.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();addServeCustom()}};customRow.append(custom,addCustom);serveBody.append(chips,suggestionTitle,suggestions,customRow);updateServeWith();
let linkedMealDraft=Array.isArray(m.linkedMealIds)?[...m.linkedMealIds]:[];
const linkedButton=$('editLinkedMeals');linkedButton.hidden=true;linkedButton.readDraft=()=>[...linkedMealDraft];linkedButton.writeDraft=ids=>{linkedMealDraft=[...ids];updateLinkedLabel()};const linkedBody=linkedButton.parentElement,linkedSearch=document.createElement('input'),linkedList=document.createElement('div');
linkedSearch.type='search';linkedSearch.placeholder='Search linked meals';linkedSearch.setAttribute('aria-label','Search linked meals');linkedList.className='meal-editor-linked-list';linkedBody.append(linkedSearch,linkedList);
function updateLinkedLabel(){document.querySelector('#editor .editor')?.refreshIndicators?.()}
buildGroupedMealPicker(linkedList,linkedSearch,meals.filter(option=>option.id!==m.id&&!option._scheduledEditorDraft&&typeof option.name==='string'&&option.name.trim()&&!(m.linkGroup&&option.linkGroup===m.linkGroup)).map(option=>({meal:option,checked:linkedMealDraft.some(id=>String(id)===String(option.id)),onChange(checked){linkedMealDraft=linkedMealDraft.filter(id=>String(id)!==String(option.id));if(checked)linkedMealDraft.push(option.id);updateLinkedLabel()}})),{checked:false},true,false,false,true,true);linkedList.collapseMealGroups();
let ingredientImportUrl=String(m.ingredientImportUrl||'');let importedRecipeDetailsDraft=null;
const ingredientField=$('ingredients');
function draftIngredientLines(){return ingredientField.value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean)}
function updateIngredientDisplay(){
  const present=draftIngredientLines().length>0;
  $('toggleIngredients').textContent='Ingredients';
  $('ingredientsLabel').classList.toggle('hidden',!present);document.querySelector('#editor .editor')?.refreshIndicators?.();
}
function displayIngredients(open,remember=true){
  $('editorIngredientsSection').open=open;
  $('ingredientsPanel').classList.toggle('hidden',!open);
  updateIngredientDisplay();
}
function applyImportedRecipeDraft(details){
 if(!details)return;importedRecipeDetailsDraft={...(importedRecipeDetailsDraft||{}),...details};
 if(!$('name').value.trim()&&details.name)$('name').value=details.name;
 if(!$('recipeInstructions').value.trim()&&details.instructions?.length)$('recipeInstructions').value=instructionEditorText(details.instructions);
 if(!$('recipeNotes').value.trim()&&details.notes)$('recipeNotes').value=details.notes;
 for(const [field,key] of [['prep','prep'],['totaltime','total'],['marinate','marinate']])if(!$(field).value.trim()&&details[key]!==''&&details[key]!=null)$(field).value=String(details[key]);
}
function mergeIngredientDraft(lines){
  const merged=uniqueIngredientLines([...draftIngredientLines(),...lines],Infinity);
  ingredientField.value=merged.join('\n');
  updateIngredientDisplay();
}
ingredientField.addEventListener('input',updateIngredientDisplay);
updateIngredientDisplay();
$('toggleIngredients').onclick=()=>displayIngredients(true);
$('hideIngredients').onclick=()=>displayIngredients(false);$('editorIngredientsSection').addEventListener('toggle',()=>displayIngredients($('editorIngredientsSection').open,false));displayIngredients(false,false);installInstructionPhotoControls(m);
$('ingredientLinkButton').onclick=async()=>{
  const recipeUrl=$('url').value.trim();
  let importUrl=null,choice='other';
  if(recipeUrl){
    choice=await selectIngredientImportSource(true);
    if(!choice||editId!==m.id)return;
    importUrl=choice==='recipe'?recipeUrl:await requestIngredientSourceUrl(ingredientImportUrl,true);
  }else{
    // No saved recipe URL: go straight to link entry; don't display a
    // disabled "Import from recipe link" choice.
    importUrl=await requestIngredientSourceUrl(ingredientImportUrl,false);
    if(!importUrl||editId!==m.id)return;
    const useAsRecipe=await askUseIngredientLinkAsRecipe();
    if(editId!==m.id)return;
    if(useAsRecipe)$('url').value=importUrl;
  }
  if(!importUrl||editId!==m.id)return;
  const progress=showImportProgressDialog();
  try{
    const result=await Promise.race([importIngredientsFromWebsite(importUrl,progress.signal).then(lines=>({lines})),progress.cancelled]);
    if(!result.cancelled&&editId===m.id&&ingredientField.isConnected){
      mergeIngredientDraft(result.lines.map(cleanImportedIngredientDescriptors));
      applyImportedRecipeDraft(result.lines.recipeDetails);
      // The import source remains independently editable from the recipe URL.
      ingredientImportUrl=choice==='other'?importUrl:'';
    }
  }catch(e){
    if(!progress.signal.aborted&&editId===m.id)showAppMessage(e.message||'Ingredients could not be imported. You can type them manually.');
  }finally{progress.close()}
};
async function importFromIngredientPhoto(file){
  if(!file||!file.type.startsWith('image/'))return;
  const progress=showImportProgressDialog('Reading ingredients from photo…');
  let deadline=null;
  try{
    // OCR can hang for an empty or extremely difficult picture on some phones.
    // Finish with a useful message instead of leaving the progress box open.
    const timedOut=new Promise(resolve=>{
      deadline=setTimeout(()=>resolve({timedOut:true}),60000);
    });
    const result=await Promise.race([
      (async()=>{
        if(await ingredientPhotoIsBlank(file))return {blank:true};
        if(progress.signal.aborted)return {cancelled:true};
        return {text:await recognizeIngredientPhoto(file,progress.signal)};
      })(),
      progress.cancelled,
      timedOut
    ]);
    if(result.timedOut)progress.abort();
    progress.close();
    if(result.cancelled||editId!==m.id||!ingredientField.isConnected)return;
    if(result.timedOut){
      await showAppMessage('The photo could not be read in time. Try a closer photo of the ingredients or enter them manually.');
      return;
    }
    if(result.blank){
      await showAppMessage('No readable ingredients found in that photo. Try a photo containing an ingredient list.');
      return;
    }
    const originalText=String(result.text||'').trim();
    if(!originalText){await showAppMessage('No readable text was found in the photo. Try a clearer picture or enter ingredients manually.');return}
    const extracted=extractPhotoIngredientLines(originalText);
    if(!extracted.lines.length){await showAppMessage('No clear ingredient list was found. Try a close-up photo of just the ingredients, or enter them manually.');return}
    const reviewed=await reviewPhotoIngredients(extracted.lines.join('\n'),originalText);
    if(reviewed!==null&&editId===m.id&&ingredientField.isConnected){mergeIngredientDraft(reviewed.split(/\r?\n/));applyImportedRecipeDraft(recipeTextSections(originalText))}
  }catch(e){
    progress.close();
    if(!progress.signal.aborted&&editId===m.id)await showAppMessage('Photo ingredients could not be read. Check your connection or enter them manually.');
  }finally{
    if(deadline!==null)clearTimeout(deadline);
    progress.close();
  }
}
$('ingredientGalleryInput').onchange=e=>{const file=e.target.files?.[0];e.target.value='';if(file)importFromIngredientPhoto(file)};
$('ingredientCameraInput').onchange=e=>{const file=e.target.files?.[0];e.target.value='';if(file)importFromIngredientPhoto(file)};
$('ingredientPhotoButton').onclick=()=>$('ingredientGalleryInput').click();
$('ingredientCameraButton').onclick=()=>$('ingredientCameraInput').click();
installRecipeIngredientLinkEditor(m);
const indicatorRoot=document.querySelector('#editor .editor');
indicatorRoot.refreshIndicators=()=>{
 const names=normalizeServeWith(serveWithDraft),linked=new Set(linkedMealDraft.map(String)),count=meals.filter(record=>linked.has(String(record.id))).length;
 const values={serve:names.length===1?names[0]:names.length?names.length+' selected':'',linked:count?count+' linked':'',recipe:[$('ingredients').value,$('recipeInstructions').value,$('url').value,$('editNeedsTweakingNote').value].some(value=>value.trim())||$('editNeedsTweaking').checked?'Added':'',notes:$('recipeNotes').value.trim()||$('recipeMakeAhead').readDraft().length?'Added':''};
 for(const [key,value]of Object.entries(values)){const label=indicatorRoot.querySelector('[data-editor-summary="'+key+'"]');if(label&&label.textContent!==value)label.textContent=value}
};
indicatorRoot.addEventListener('input',indicatorRoot.refreshIndicators);indicatorRoot.addEventListener('change',indicatorRoot.refreshIndicators);indicatorRoot.refreshIndicators();
const savedEditorDraft={name:$('name').value,prep:$('prep').value,total:$('totaltime').value,marinate:$('marinate').value,ingredients:$('ingredients').value,instructions:$('recipeInstructions').value,notes:$('recipeNotes').value,url:$('url').value,serveWith:JSON.stringify(serveWithDraft),linked:JSON.stringify(linkedMealDraft),tasks:JSON.stringify($('recipeMakeAhead').readDraft()),adjusting:$('editNeedsTweaking').checked,adjustingNote:$('editNeedsTweakingNote').value};
const persistenceEditor=document.querySelector('#editor .editor');
const captureEditorRecoveryDraft=()=>({recipeId:String(m.id),rawControls:[...persistenceEditor.querySelectorAll('input:not([type=file]),textarea,select')].map(el=>({id:el.id,name:el.name,value:el.value,checked:el.checked})),originalRecipe:JSON.parse(JSON.stringify(m)),fields:Object.fromEntries(['name','prep','totaltime','marinate','ingredients','recipeInstructions','recipeNotes','url','editNeedsTweakingNote'].map(id=>[id,$(id)?.value??''])),rotation:$('rotation')?.checked,needsTweaking:$('editNeedsTweaking')?.checked,memberships:JSON.parse(JSON.stringify(editorMembershipDraft)),newGroups:pendingEditorGroups.filter(cat=>editorDraftCategories.includes(cat)),serveWith:[...serveWithDraft],linkedMealIds:[...linkedMealDraft],makeAheadTasks:$('recipeMakeAhead')?.readDraft?.()||[],ingredientStepLinks:$('recipeIngredientLinks')?.captureRecoveryDraft?.(),ingredientImportUrl,importedRecipeDetails:importedRecipeDetailsDraft});
persistenceEditor.mealRecoveryDraft={ownerId:'recipe:'+m.id,kind:'recipe-editor',capture:captureEditorRecoveryDraft,dirty:editorHasPendingChanges,save:()=>$('save')?.onclick?.(),discard:()=>$('cancel')?.onclick?.()};
// Use a current editor handler for Retry Save. A confirmation must not commit an older draft.
let persistenceEditorSaving=false;
$('save').onclick=async()=>{
 if(persistenceEditorSaving)return;
 persistenceEditorSaving=true;
 try{
  const validatedDraftFingerprint=JSON.stringify(captureEditorRecoveryDraft());
  // Check all time inputs before mutating any stored meal data.
  const prepInput=parseDurationInput($('prep').value);
  const totalInput=parseDurationInput($('totaltime').value);
  const marinateInput=parseMarinateInput($('marinate').value);
  if(Number.isNaN(prepInput)||Number.isNaN(totalInput)||Number.isNaN(marinateInput)){
    const field=Number.isNaN(prepInput)?$('prep'):Number.isNaN(totalInput)?$('totaltime'):$('marinate');
    await showAppMessage('Please enter a valid time, such as 30 min, 2 hrs, 1 hr 30 min, or a marinate range like 30 min - 3 hrs.');
    revealMealEditorField(field);return;
  }
  const prepValue=prepInput===null?'':String(prepInput);
  const totalValue=totalInput===null?'':String(totalInput);
  const marinateValue=marinateInput===null?'':$('marinate').value.trim();
  const nextNeedsTweaking=$('editNeedsTweaking').checked,nextTweakingNote=$('editNeedsTweakingNote').value===String(m.needsTweakingNote||'')?String(m.needsTweakingNote||''):$('editNeedsTweakingNote').value.trim();
  const originalIngredients=Array.isArray(m.ingredients)?m.ingredients:[];
  const nextIngredients=draftIngredientLines();
  const nextInstructions=$('recipeInstructions').value===instructionEditorText(m.instructions)?instructionBlocks(m.instructions):instructionBlocks($('recipeInstructions').value);
  const nextNotes=$('recipeNotes').value===String(m.notes||'')?String(m.notes||''):$('recipeNotes').value.trim();
  const nextIngredientLinks=$('recipeIngredientLinks').getLinks({...m,ingredients:nextIngredients,instructions:nextInstructions});
  const cookValue=prepValue===String(m.prep??'')&&totalValue===String(m.total!==undefined&&m.total!==''?m.total:(m.prep!==''||m.cook!==''?(Number(m.prep)||0)+(Number(m.cook)||0):''))?(m.cook??''):'';

  const nextMakeAhead=$('recipeMakeAhead').readDraft();if(!$('recipeMakeAhead').validDraft()){await showAppMessage('Enter a valid preparation lead time: positive hours or days, or 0 days for the same day (up to 36600 days).');revealMealEditorField($('recipeMakeAhead'));return}
  const next={...m,name:$('name').value.trim()||'Untitled meal',prep:prepValue,total:totalValue,marinate:marinateValue,cook:cookValue,url:$('url').value.trim(),ingredientImportUrl,ingredients:nextIngredients,instructions:nextInstructions,notes:nextNotes,linkedMealIds:[...linkedMealDraft],serveWith:[...serveWithDraft]};
  if(next.url!==String(m.url||'')){next.originalRecipeUrl=next.url;next.recipeSourceHidden=!next.url}
  if(nextIngredientLinks.length||Array.isArray(m.ingredientStepLinks))next.ingredientStepLinks=nextIngredientLinks;
  if(importedRecipeDetailsDraft?.recipeImportReferences?.length||$('recipeInstructions').recipeImportReferences?.length)next.recipeImportReferences=mergeRecipeImportReferences(m.recipeImportReferences||[],importedRecipeDetailsDraft?.recipeImportReferences||[],$('recipeInstructions').recipeImportReferences||[]);if(importedRecipeDetailsDraft?.originalRecipeUrl)next.originalRecipeUrl=importedRecipeDetailsDraft.originalRecipeUrl;
  if(nextMakeAhead.length||Array.isArray(m.makeAheadTasks))next.makeAheadTasks=nextMakeAhead;
  if(nextNeedsTweaking)next.needsTweaking=true;else delete next.needsTweaking;
  if(nextTweakingNote||nextNeedsTweaking||Object.hasOwn(m,'needsTweakingNote'))next.needsTweakingNote=nextTweakingNote;else delete next.needsTweakingNote;
  const removed=editorMembershipDraft.filter(draft=>draft.id!==null&&!draft.cat&&meals.some(record=>String(record.id)===String(draft.id)&&record.cat)).map(draft=>String(draft.id)),scheduled=mealPlans.flatMap(plan=>getDisplayedWeekdayMealsForPlan(plan)).some(entry=>removed.includes(String(entry.meal.id))),referenced=meals.some(record=>(record.linkedMealIds||[]).some(id=>removed.includes(String(id))));
  if(removed.length&&(scheduled||referenced)&&await appDialog('Remove from group?',null,'tracking-remove',[],'Only this recipe’s selected group memberships will be removed. The recipe stays in your collection. If it has no groups left, it moves to Unassigned. Scheduled slots and references use the existing replacement and cleanup rules.')!==true)return;
  if(!persistenceEditor.isConnected||editId!==m.id)return;
  if(JSON.stringify(captureEditorRecoveryDraft())!==validatedDraftFingerprint){await showAppMessage('Your draft changed while confirmation was open. Your latest changes are still here; save again to validate them.');return}
  const fields=sharedRecipeChanges(m,next);for(const [field,key]of [['name','name'],['marinate','marinate'],['ingredients','ingredients'],['instructions','recipeInstructions'],['notes','recipeNotes'],['url','url']])if($(key).value===savedEditorDraft[field])delete fields[field];if($('prep').value===savedEditorDraft.prep&&$('totaltime').value===savedEditorDraft.total){delete fields.prep;delete fields.total;delete fields.cook}if(JSON.stringify(serveWithDraft)===savedEditorDraft.serveWith)delete fields.serveWith;if(JSON.stringify(linkedMealDraft)===savedEditorDraft.linked)delete fields.linkedMealIds;if(JSON.stringify(nextMakeAhead)===savedEditorDraft.tasks)delete fields.makeAheadTasks;if($('editNeedsTweaking').checked===savedEditorDraft.adjusting&&$('editNeedsTweakingNote').value===savedEditorDraft.adjustingNote){delete fields.needsTweaking;delete fields.needsTweakingNote}if(!$('recipeIngredientLinks').hasChanges()&&!fields.ingredients&&!fields.instructions)delete fields.ingredientStepLinks;
  if(newRecipeDraftId===m.id)fields.keepAsIdea=!$('rotation').checked;
  if(scheduledMealEditor?.draftId===m.id){try{saveScheduledMealEditor(next,editorMembershipDraft,$('rotation').checked)}catch(error){await showAppMessage('Meal could not be saved: '+error.message+' Your draft is still open.')}return}
  try{applyRecipeBulk([String(m.id)],{}, {render:false,editor:{sourceId:String(m.id),memberships:editorMembershipDraft.map(draft=>({...draft})),newGroups:pendingEditorGroups.filter(cat=>editorDraftCategories.includes(cat)),fields,rotation:$('rotation').checked}})}catch(e){await showAppMessage('Recipe could not be saved: '+e.message+' Your draft is still open.');return}
  const saved=meals.find(record=>String(record.id)===String(m.id));
  const chooseFirstGroup=newRecipeDraftId===m.id&&saved?.cat===''&&meals.length===1;
  if(newRecipeDraftId===m.id){
   newRecipeDraftId=null;
   if(saved?.cat===''&&mealEditorReturnView){
    mealEditorReturnView={...mealEditorReturnView,view:'groups',expandedCategories:[''],expansionInitialized:true,scroll:0};
    mealEditorReturnScroll=0;
   }
  }
  editorCategoryBaseline=null;editorDraftCategories=null;editId=null;if(tutorialStage==='editing')setTutorialStage('3');restoreMealEditorScroll();
  if(chooseFirstGroup)chooseGroupForFirstMeal(saved);
  else if(saved&&importedRecipeDetailsDraft?.recipeImportReferences?.length)recipeImportNotice('Related recipe references were found. No new links have been selected.',[saved]);

 }finally{persistenceEditorSaving=false}
};
$('cancel').onclick=()=>{mealPersistence.cancelOwner('recipe:'+m.id);rollbackEditorCategories();editId=null;if(tutorialStage==='editing')setTutorialStage('2');restoreMealEditorScroll()};$('delete').onclick=async()=>{const ids=await confirmDeleteRecipes([String(m.id)]);if(!ids)return;try{applyRecipeBulk(ids,{delete:true},{render:false})}catch(e){await showAppMessage('Recipe could not be deleted: '+e.message);return}if(newRecipeDraftId===m.id)newRecipeDraftId=null;editorCategoryBaseline=null;editorDraftCategories=null;editId=null;restoreMealEditorScroll()};installEditableMealCard(m);decorateScheduledMealEditor()}function installEditableMealCard(meal){
 const root=document.querySelector('#editor .editor'),fields=root.querySelector('.meal-editor-fields');let card=mealEditorRow();
 if(card){const anchor=document.createElement('div');anchor.dataset.mealEditorAnchor=String(meal.id);card.before(anchor)}
 else{card=document.createElement('div');card.className='master-category-meal';card.dataset.mealId=String(meal.id);const info=document.createElement('div');info.className='master-meal-info';card.append(info)}
 card.classList.add('meal-card-edit-mode');const tint=getComputedStyle(card).backgroundColor;card.style.setProperty('--meal-edit-field','color-mix(in srgb, '+tint+' 55%, white)');fields.prepend(card);const info=card.querySelector('.master-meal-info');
 const nameInput=$('name'),nameLabel=root.querySelector('label[for="name"]');nameLabel?.remove();nameInput.setAttribute('aria-label','Meal name');
 const nameSlot=document.createElement('div');nameSlot.className='meal-card-name-field';const nameButton=document.createElement('button');nameButton.type='button';nameButton.className='master-category-meal-name meal-card-field-button';nameButton.setAttribute('aria-label','Edit meal name');const nameText=document.createTextNode('');nameButton.append(nameText);nameSlot.append(nameButton,nameInput);
 const warning=document.createElement('span');warning.className='meal-card-adjusting-warning';warning.innerHTML=needsTweakingIconSvg();warning.setAttribute('aria-label','Needs Adjusting');nameSlot.append(warning);
 const times=document.createElement('div');times.className='times meal-card-times';const bindings=[];
 function bind(input,button,title,caption){
  input.hidden=true;input.setAttribute('aria-label',title);button.onclick=()=>open();
  const close=()=>{if(input.hidden)return;input.hidden=true;button.hidden=false;root.querySelector('.time-keyboard-tools')?.classList.add('hidden');refresh()};
  const open=()=>{for(const other of bindings)other.close();input.hidden=false;button.hidden=true;input.focus({preventScroll:true});input.select()};
  input.revealCardField=open;input.addEventListener('blur',event=>{if(!event.relatedTarget?.closest?.('.time-keyboard-tools'))close()});input.addEventListener('keydown',event=>{if(['Enter','Escape'].includes(event.key)){event.preventDefault();event.stopPropagation();close();button.focus({preventScroll:true})}});
  bindings.push({input,button,caption,close,open});return open;
 }
 const nameOpen=bind(nameInput,nameButton,'Meal name',null);
 for(const [id,title,caption]of [['prep','Prep time','prep'],['totaltime','Total time','total'],['marinate','Marinate time','marinate']]){
  const input=$(id);root.querySelector('label[for="'+id+'"]')?.remove();const slot=document.createElement('span');slot.className='meal-card-time-field';const button=document.createElement('button');button.type='button';button.className='meal-card-field-button';button.setAttribute('aria-label','Edit '+title.toLowerCase());slot.append(button,input);times.append(slot);bind(input,button,title,caption);
 }
 root.querySelector('.time-editor-grid')?.remove();const keyboard=root.querySelector('.time-keyboard-tools');keyboard?.addEventListener('pointerdown',event=>{if(event.target.closest('button'))event.preventDefault()});
 const linked=document.createElement('div');linked.id='mealCardLinkedPicker';linked.className='meal-editor-subsection meal-card-linked';
 const summary=document.createElement('button');summary.type='button';summary.className='meal-linked-picker-trigger';const linkedHeading=document.createElement('strong'),linkedText=document.createElement('span'),linkedAction=document.createElement('span');linkedHeading.textContent='Linked Recipes';linkedHeading.className='meal-card-linked-heading';linkedText.className='meal-card-linked-names';linkedAction.className='meal-card-links-action';summary.setAttribute('aria-label','Edit linked recipes');summary.append(linkedHeading,linkedText,linkedAction);linked.append(summary);
 summary.setAttribute('aria-haspopup','dialog');
 summary.onclick=()=>{
  const d=recipeBulkDialog('Select Linked Recipes',()=>summary),list=document.createElement('div');
  list.className='meal-group-picker-options meal-linked-dialog-options';
  list.setAttribute('role','group');list.setAttribute('aria-label','Linked Recipes');
  const selected=new Set($('editLinkedMeals').readDraft().map(String));
  const search=document.createElement('input');search.type='search';search.placeholder='Search linked recipes';search.setAttribute('aria-label','Search linked recipes');search.className='meal-linked-dialog-search';
  const options=meals.filter(option=>option.id!==meal.id&&!option._scheduledEditorDraft&&typeof option.name==='string'&&option.name.trim()&&!(meal.linkGroup&&option.linkGroup===meal.linkGroup));
  for(const option of options){const label=document.createElement('label'),check=document.createElement('input'),name=document.createElement('span');check.type='checkbox';check.value=String(option.id);check.checked=selected.has(String(option.id));name.textContent=option.name;label.append(check,name);check.onchange=()=>{if(check.checked)selected.add(check.value);else selected.delete(check.value)};list.append(label)}
  search.oninput=()=>{const term=search.value.trim().toLocaleLowerCase();for(const label of list.children)label.hidden=!!term&&!label.textContent.toLocaleLowerCase().includes(term)};
  const actions=document.createElement('div');actions.className='meal-linked-dialog-actions';
  const apply=document.createElement('button');apply.type='button';apply.className='iconbtn';setIconButton(apply,'save','Apply linked recipes');apply.onclick=()=>{
   const ids=options.filter(option=>selected.has(String(option.id))).map(option=>option.id);
   $('editLinkedMeals').writeDraft(ids);d.close();
  };
  const cancel=document.createElement('button');cancel.type='button';cancel.className='iconbtn';setIconButton(cancel,'cancel','Close without changes');cancel.onclick=d.close;
  actions.append(apply,cancel);d.panel.append(search,list,actions);d.overlay.classList.add('meal-linked-dialog');fitOneTimeMealViewport(d.overlay,d.panel);cancel.focus({preventScroll:true});
 };
 const cooked=info.querySelector('.meal-last-cooked');info.replaceChildren(nameSlot,times);if(keyboard)info.append(keyboard);const rotationControl=root.querySelector('.meal-card-rotation-control');if(rotationControl)info.append(rotationControl);card.after(linked);if(cooked)info.append(cooked);
 function refresh(){
  nameText.data=nameInput.value.trim()||'Untitled meal';warning.hidden=!$('editNeedsTweaking').checked;
  for(const item of bindings)if(item.caption){const value=item.input.value.trim(),parsed=item.caption==='marinate'?null:parseDurationInput(value);item.button.textContent=(value?(item.caption==='marinate'?(displayMarinateTime(value)||value):Number.isFinite(parsed)?time(parsed):value):'—')+' '+item.caption}
  const ids=$('editLinkedMeals').readDraft(),names=ids.map(id=>meals.find(m=>String(m.id)===String(id))?.name).filter(Boolean);linkedText.textContent=names.length?(names[0]+(names.length>1?' +'+(names.length-1)+' more':'')):'None';linkedText.hidden=false;linkedAction.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'+appIconSvg.add+'</svg>';linkedAction.setAttribute('aria-label',names.length?'Edit linked meals':'Add linked meals');
 }
 root.addEventListener('input',refresh);root.addEventListener('change',refresh);root.refreshCard=refresh;
 const originalRefresh=root.refreshIndicators;root.refreshIndicators=()=>{originalRefresh?.();refresh()};refresh();if(!meal.name?.trim())nameOpen();
}
function placeEditorInline(){
 if(scheduledMealEditor?.dialog){scheduledMealEditor.dialog.panel.append($('editor'));return}
 const editor=$('editor'),row=document.querySelector('[data-meal-editor-anchor="'+editId+'"]')||mealEditorRow();
 if(row&&row.parentNode&&!editor.contains(row))row.insertAdjacentElement('afterend',editor);
 else if(editor.parentNode!==document.body)document.body.insertBefore(editor,$('list'));
}

function render(){repairImportedRecipeSageLinks();if(!showTop&&!masterCategoriesView)setMasterCategoriesView(true);if(!showTop&&!masterExpansionInitialized){masterExpansionInitialized=true;masterExpandedCategories.clear();}persist();rememberCurrentView();renderTabs();renderMenu();renderList();if(editId){renderEditor();placeEditorInline()}else{$('editor').innerHTML='';const e=$('editor');if(e.parentNode!==document.body)document.body.insertBefore(e,$('list'))}requestAnimationFrame(showTutorialHint);requestRecipeImportResume()}document.addEventListener('contextmenu',e=>{if(!e.target.closest('input,textarea,select')){e.preventDefault();e.stopPropagation()}});document.addEventListener('selectstart',e=>{if(!e.target.closest('input,textarea,select'))e.preventDefault()});document.addEventListener('pointerdown',e=>{if(menuCat&&!$('catmenu').classList.contains('hidden')&&!$('catmenu').contains(e.target)&&!$('tabs').contains(e.target)){menuCat=null;renderMenu()}});
// Outside-tap handling for inline meal editors and both settings panels.
// A single tap should first close the open pane, then perform the tapped action.
// When there are edits, finish the confirmation before replaying that tap.
function editorHasPendingChanges(){
 if(editId===null||!document.querySelector('#editor .editor'))return false;
 if(scheduledMealEditor&&scheduledMealEditor.oneTime!==!!scheduledMealEditor.current)return true;
 const meal=meals.find(m=>m.id===editId);if(!meal)return false;
 const byId=id=>document.getElementById(id);
 const prep=parseDurationInput(byId('prep')?.value||'');
 const total=parseDurationInput(byId('totaltime')?.value||'');
 const storedTotal=meal.total!==undefined&&meal.total!==''?meal.total:(meal.prep!==''||meal.cook!==''?(Number(meal.prep)||0)+(Number(meal.cook)||0):'');
 const oldCats=[...new Set((meal.linkGroup?meals.filter(x=>x.linkGroup===meal.linkGroup):[meal]).map(x=>x.cat).filter(Boolean))].sort();
 const newCats=[...(editorDraftCategories||[])].sort();
 return (byId('name')?.value.trim()||'Untitled meal')!==(meal.name||'Untitled meal')||
   (Number.isNaN(prep)||String(prep??'')!==String(meal.prep??''))||
   (Number.isNaN(total)||String(total??'')!==String(storedTotal))||
   (byId('marinate')?.value.trim()||'')!==String(meal.marinate||'')||
   (byId('url')?.value.trim()||'')!==String(meal.url||'')||
   (byId('recipeInstructions')?.value||'')!==instructionEditorText(meal.instructions)||
   (byId('recipeNotes')?.value||'')!==String(meal.notes||'')||
   !!byId('editNeedsTweaking')?.checked!==(meal.needsTweaking===true)||
   ((byId('editNeedsTweakingNote')?.value||'')!==String(meal.needsTweakingNote||''))||
   JSON.stringify(byId('recipeMakeAhead')?.readDraft?.()||[])!==JSON.stringify(recipeMakeAheadTasks(meal))||
   JSON.stringify(byId('serveWith')?.readDraft?.()||[])!==JSON.stringify(meal.serveWith||[])||
   JSON.stringify(byId('editLinkedMeals')?.readDraft?.()||[])!==JSON.stringify(meal.linkedMealIds||[])||
   !!byId('recipeIngredientLinks')?.hasChanges?.()||
   !!byId('rotation')?.checked!==(!!meal.rotation||newRecipeDraftId===meal.id)||
   JSON.stringify((byId('ingredients')?.value||'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean))!==JSON.stringify((meal.ingredients||[]).map(removeIngredientListMarker).map(x=>String(x).trim()).filter(Boolean))||
   JSON.stringify(oldCats)!==JSON.stringify(newCats);
}
let replayingOutsidePaneClick=false;
// A tap on a recipe name while dismissing Settings must NOT also open its link.
// Other outside taps (switch view/category, select a tab, etc.) still take effect.
function isRecipeLinkOutsideTap(target){
 const name=target instanceof Element?target.closest('.mealname'):null;
 if(!name)return false;
 const row=name.closest('[data-meal-id]');
 const mealId=row?.dataset.mealId;
 const meal=mealId===undefined?null:meals.find(m=>String(m.id)===mealId);
 return !!(meal&&meal.url);
}
function performOutsideAction(originalTarget){
 // Use the original control's handler: it retains its delegated/closure action
 // even if a redraw replaced the element during the confirmation dialogue.
 const control=originalTarget instanceof Element?(originalTarget.closest('button,a,input,select,[role="button"]')||originalTarget):originalTarget;
 if(!control||typeof control.click!=='function')return;
 replayingOutsidePaneClick=true;
 try{control.click()}finally{replayingOutsidePaneClick=false}
}
document.addEventListener('click',e=>{
 if(replayingOutsidePaneClick||!(e.target instanceof Element))return;
 // An existing modal (e.g. a recipe import or deletion confirmation) owns its taps.
 if(e.target.closest('[role="dialog"],[role="alertdialog"],#categoryDeleteDialog,#mealSwipeMenu,#mealSaveWarning,#mealDataRecovery'))return;
 const upper=document.getElementById('settingsPanel');
 const lower=document.getElementById('planSettingsPanel');
 const editor=document.querySelector('#editor .editor');
 const insideSettings=(upper&&!upper.classList.contains('hidden')&&upper.contains(e.target))||
                      (lower&&!lower.classList.contains('hidden')&&lower.contains(e.target));
 const onSettingsToggle=!!e.target.closest('#settings,#planSettings');
 const closeSettings=settingsBaseline!==null&&!insideSettings&&!onSettingsToggle;
 const closeEditor=editId!==null&&!!editor&&!editor.contains(e.target);
 if(!closeSettings&&!closeEditor)return;
 const needsConfirmation=(closeSettings&&settingsAreDirty())||(closeEditor&&editorHasPendingChanges());
 const suppressRecipeLink=closeSettings&&isRecipeLinkOutsideTap(e.target);
 if(!needsConfirmation){
  if(suppressRecipeLink){e.preventDefault();e.stopImmediatePropagation();}
  // Synchronous closure leaves the original click to perform its intended action.
  if(closeSettings)finishSettings('save');
  if(closeEditor){if(window.history.state?.mealRotationEditor){e.preventDefault();e.stopImmediatePropagation();const clicked=e.target;closeMealEditorWithPrompt().then(closed=>{if(closed&&!suppressRecipeLink)performOutsideAction(clicked)});return}rollbackEditorCategories();editId=null;document.getElementById('editor').innerHTML='';restoreMealEditorScroll()}
  return;
 }
 e.preventDefault();e.stopImmediatePropagation();
 const clicked=e.target;
 (async()=>{
  if(closeSettings)await finishSettings('ask');
  if(closeEditor&&editId!==null&&!await closeMealEditorWithPrompt())return;
  if(closeEditor&&editId===null&&mealEditorReturnView)restoreMealEditorScroll();else render();
  if(!suppressRecipeLink)performOutsideAction(clicked);
 })().catch(err=>{console.error('Could not complete outside action',err)});
},true);

mealPersistence.showRecovery({normalize:normalizeImportedBackup,validate:validateBackupStorage,validateCore:d=>validateBackupStorage(normalizeImportedBackup(d))});
if(!mealPersistence.recovery){
 try{rotationCalendarTrackingReady=true;render();window.history.replaceState({...window.history.state,mealRotationView:appViewSnapshot()},'');syncCookingTimer();syncMakeAheadLocalDay()}catch(error){mealPersistence.failStartup(error)}
 if(!mealPersistence.recovery){showRecipePhotoRestoreNotice();resumeRecipeViewer()}
}

/* Detect when each page-specific header actually reaches its sticky position.
   Page renders replace these elements, so re-evaluate after DOM changes. */
(()=>{
  const selector='#list .rotation-compact-header, #list .meal-plan-grocery .grocery-compact-header, #list .all-meals-overview > h2';
  let queued=false;
  function update(){
    queued=false;
    document.querySelectorAll(selector).forEach(header=>{
      const stickyTop=parseFloat(getComputedStyle(header).top)||0;
      const stuck=window.scrollY>0 && header.getBoundingClientRect().top<=stickyTop+1;
      header.classList.toggle('is-stuck',stuck);
    });
  }
  function schedule(){if(!queued){queued=true;requestAnimationFrame(update)}}
  window.addEventListener('scroll',schedule,{passive:true});
  window.addEventListener('resize',schedule,{passive:true});
  const list=document.getElementById('list');
  if(list)new MutationObserver(schedule).observe(list,{childList:true,subtree:true});
  schedule();
})();
