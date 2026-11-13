/* First-run UI and compact sample data. Classic script; no dependency or build step. */
const ONBOARDING_SAMPLE_KEY='mealRotationSampleWeekLoadedV1';
const ONBOARDING_DISMISSED_KEY='mealRotationOnboardingHintDismissedV1';
let onboardingStarting=false,onboardingHintDismissed=false;
try{onboardingHintDismissed=window.localStorage.getItem(ONBOARDING_DISMISSED_KEY)==='true'}catch(_){}

function onboardingHasAssignments(value){
 return !!value&&typeof value==='object'&&Object.values(value).some(items=>
  (Array.isArray(items)?items:[items]).some(item=>typeof item==='string'&&item.trim()&&item!==EMPTY_DAY_ASSIGNMENT));
}
function isOnboardingZeroState(){
 if(mealPersistence.paused||cats.length||meals.length||onboardingHasAssignments(weekdayCategories))return false;
 try{
  // Re-read persisted data as well as memory: a second tab may have added recipes.
  const raw=window.localStorage.getItem('mealRotationDataV1');
  if(raw!==null){
   const core=JSON.parse(raw);
   if(!Array.isArray(core.cats)||!Array.isArray(core.meals)||core.cats.length||core.meals.length)return false;
  }
  const assignments=JSON.parse(window.localStorage.getItem('mealRotationWeekdayCategoriesV1')||'null');
  const plans=JSON.parse(window.localStorage.getItem('mealRotationPlansV1')||'null');
  if(onboardingHasAssignments(assignments))return false;
  if(plans!==null&&!Array.isArray(plans.plans))return false;
  return !(plans?.plans||mealPlans).some(plan=>
   onboardingHasAssignments(plan.weekdayCategories)||
   Object.keys(plan.weekdayMealOverrides||{}).length||
   Object.keys(plan.occasionalMeals||{}).length||
   Object.values(plan.weekSchedule?.slots||{}).some(slot=>slot?.kind==='once'));
 }catch(_){return false} // Unreadable storage is recovery, never permission to seed.
}
function sampleWeekBackup(){
 const groups=['Quick Pasta','Sheet Pan','Tacos & Bowls','Stir-Fry','Slow Cooker / Soup','Leftovers / Takeout','Grill / Skillet'];
 const rows=[
  ['Quick Pasta','Tomato & chickpea pasta',['200 g pasta','1 can chickpeas, drained','1 can chopped tomatoes','1 tbsp olive oil'],
   ['Boil pasta until tender.','Warm oil, tomatoes and chickpeas for 10 minutes. Toss with drained pasta.']],
  ['Quick Pasta','Lemon pea pasta',['200 g pasta','1 cup frozen peas','1 lemon','2 tbsp olive oil'],
   ['Boil pasta; add peas for the final 2 minutes.','Drain, reserving a little water. Toss with oil, lemon zest and juice.']],
  ['Sheet Pan','Sheet-pan chicken & potatoes',['2 chicken thighs','2 potatoes, diced small','2 carrots, sliced','1 tbsp olive oil','1 tsp paprika'],
   ['Heat oven to 220°C / 425°F. Toss everything with oil and paprika on a sheet pan.','Roast for 30–40 minutes, until potatoes are tender and chicken reaches 74°C / 165°F.']],
  ['Tacos & Bowls','Black bean taco bowls',['1 can black beans, drained','1 cup dry rice','1 cup salsa','1 avocado'],
   ['Cook rice according to the package.','Heat beans with salsa. Serve over rice with sliced avocado.']],
  ['Tacos & Bowls','Easy turkey tacos',['250 g ground turkey','1 tsp ground cumin','6 small tortillas','1 cup shredded cabbage','1/2 cup salsa'],
   ['Cook turkey with cumin in a skillet until it reaches 74°C / 165°F.','Fill warm tortillas with turkey, cabbage and salsa.']],
  ['Stir-Fry','Ginger tofu & broccoli',['250 g firm tofu, cubed','2 cups broccoli florets','1 tbsp oil','2 tbsp soy sauce','1 tsp grated ginger','1 cup dry rice'],
   ['Cook rice according to the package.','Brown tofu in oil. Add broccoli and a splash of water; cover for 4 minutes. Stir in soy sauce and ginger; serve with rice.']],
  ['Slow Cooker / Soup','One-pot lentil & tomato soup',['1 can lentils, drained','1 can chopped tomatoes','2 cups vegetable stock','2 carrots, diced','1 tsp dried herbs'],
   ['Put all ingredients in a pot and bring to a boil.','Simmer for 20 minutes, until carrots are tender. Serve with bread if you like.']],
  ['Leftovers / Takeout','Leftover veggie rice & eggs',['2 cups cooked rice, promptly chilled','2 eggs','1 cup frozen mixed vegetables','1 tbsp oil','1 tbsp soy sauce'],
   ['Use refrigerated rice within 24 hours. Heat oil and cook vegetables in a skillet.','Add rice and stir until steaming hot throughout. Push aside, scramble eggs until set, then mix with soy sauce.']],
  ['Grill / Skillet','Skillet lemon chicken',['2 chicken breasts, sliced thin','1 lemon','1 tbsp olive oil','2 cups green beans'],
   ['Brown chicken in oil, turning until it reaches 74°C / 165°F. Remove to a plate.','Add green beans and a splash of water. Cover for 5 minutes, then return chicken and finish with lemon juice.']]
 ];
 const sampleMeals=rows.map(([cat,name,ingredients,steps],index)=>({
  id:index+1,cat,name,rotation:true,ingredients,
  instructions:steps.map(text=>({type:'step',text}))
 }));
 const dayGroups=[groups[0],groups[2],groups[1],groups[3],groups[6],groups[4],groups[5]];
 const assignments=Object.fromEntries(weekdays.map((day,index)=>[day,[dayGroups[index]]]));
 // Preserve plan names, other tabs, settings and opaque extension records.
 const plans=JSON.parse(JSON.stringify(mealPlans));
 const plan=plans.find(item=>item.id===activePlanId);
 if(!plan)throw Error('The active meal plan could not be found.');
 plan.weekdayCategories=assignments;plan.weekdayMealOverrides={};plan.weekdayRecipeFilters={};
 const storage={...captureBackupStorage(),
  mealRotationDataV1:JSON.stringify({cats:groups,active:groups[0],meals:sampleMeals}),
  mealRotationWeekdayCategoriesV1:JSON.stringify(assignments),
  mealRotationWeekdayMealOverridesV1:'{}',
  mealRotationWeekdayRecipeFiltersV1:'{}',
  mealRotationPlansV1:JSON.stringify({plans,activeId:activePlanId}),
  [ONBOARDING_SAMPLE_KEY]:'true'
 };
 return {version:2,cats:groups,active:groups[0],meals:sampleMeals,
  weekdayCategories:assignments,weekdayMealOverrides:{},
  mealPlans:{plans,activeId:activePlanId},storage};
}
function quickStartSampleWeek(){
 if(onboardingStarting)return false;
 const status=document.getElementById('onboardingStatus');
 if(!isOnboardingZeroState()){
  if(status)status.textContent='Your library already has data. Nothing was changed.';
  return false;
 }
 onboardingStarting=true;
 try{
  const backup=sampleWeekBackup();
  validateBackupCore(backup);validateBackupStorage(backup.storage);
  if(!isOnboardingZeroState())throw Error('Your library changed. Nothing was added.');
  restoreBackupStorage(backup.storage,{id:'onboarding-sample-week',kind:'onboarding',ownerId:null,retry:quickStartSampleWeek});
  cats=backup.cats;active=backup.active;meals=backup.meals;id=meals.length+1;
  mealPlans=backup.mealPlans.plans;weekdayCategories=backup.weekdayCategories;
  weekdayMealOverrides={};weekdayRecipeFilters={};
  showTop=true;allMealsActive=false;groceryTabActive=false;editId=null;menuCat=null;
  render();
  const heading=document.querySelector('#list .view-page-title');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true})}
  return true;
 }catch(error){
  if(status)status.textContent='The sample week was not loaded. '+error.message+' Free some storage and try again.';
  return false;
 }finally{onboardingStarting=false}
}
function renderOnboardingWelcome(){
 const list=document.getElementById('list');
 list.classList.remove('top-summary');list.replaceChildren();
 document.querySelectorAll('.add-meal-floating').forEach(button=>button.remove());
 topPanel.classList.add('hidden');
 const card=document.createElement('section');card.id='onboardingWelcome';card.className='onboarding-welcome';
 card.setAttribute('aria-labelledby','onboardingTitle');
 const eyebrow=document.createElement('p');eyebrow.className='onboarding-eyebrow';eyebrow.textContent='A simpler dinner routine';
 const title=document.createElement('h1');title.id='onboardingTitle';title.className='onboarding-title';title.textContent='Zero-decision weekly meals, on autopilot.';
 const copy=document.createElement('p');copy.className='onboarding-copy';copy.textContent='Assign a meal category to each weekday, and your dinners rotate automatically. Less daily guesswork, more meals you already know how to make.';
 const actions=document.createElement('div');actions.className='onboarding-actions';
 const start=document.createElement('button');start.type='button';start.id='onboardingQuickStart';start.className='onboarding-primary';start.textContent='Quick-Start with Sample Week';start.onclick=quickStartSampleWeek;
 const restore=document.createElement('button');restore.type='button';restore.id='onboardingRestore';restore.className='onboarding-secondary';restore.textContent='Restore Backup (.json)';
 const status=document.createElement('p');status.id='onboardingStatus';status.className='onboarding-status';status.setAttribute('role','status');
 restore.onclick=()=>openBackupRestorePicker(error=>{status.textContent=error.message},isOnboardingZeroState);
 actions.append(start,restore);card.append(eyebrow,title,copy,actions,status);list.append(card);
}
function dismissOnboardingHint(){
 if(onboardingHintDismissed)return;
 try{if(window.localStorage.getItem(ONBOARDING_SAMPLE_KEY)!=='true')return}catch(_){return}
 onboardingHintDismissed=true;
 try{window.localStorage.setItem(ONBOARDING_DISMISSED_KEY,'true')}catch(_){/* Keep it dismissed in this tab if storage is unavailable. */}
 document.getElementById('onboardingHint')?.remove();
}
function appendOnboardingHint(parent){
 if(onboardingHintDismissed||!meals.length||allMealsActive||groceryTabActive)return;
 try{
  if(window.localStorage.getItem(ONBOARDING_DISMISSED_KEY)==='true'){onboardingHintDismissed=true;return}
  if(window.localStorage.getItem(ONBOARDING_SAMPLE_KEY)!=='true')return;
 }catch(_){return}
 const hint=document.createElement('aside');hint.id='onboardingHint';hint.className='onboarding-hint';
 const text=document.createElement('p');text.className='onboarding-hint-copy';text.setAttribute('role','status');text.textContent='Sample week loaded! Tap any day to swap meals, or customize your weekday categories anytime.';
 const close=document.createElement('button');close.type='button';close.className='onboarding-dismiss';close.setAttribute('aria-label','Dismiss sample week tip');close.textContent='×';
 close.onclick=dismissOnboardingHint;hint.append(text,close);parent.append(hint);
}
