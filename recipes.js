const RECIPE_VIEW_PREFS_KEY='mealRotationRecipeViewPrefsV1';
let recipeViewPrefs={mode:'full',ratio:.4,landscapeRatio:.5,syncIngredients:false,autoCompleteIngredients:false,keepScreenAwake:true,autoOpenLinkedRecipes:true,timerAlarmVolume:.8};
try{const p=JSON.parse(localStorage.getItem(RECIPE_VIEW_PREFS_KEY)||'null');if(p&&['full','split'].includes(p.mode)&&Number.isFinite(p.ratio))recipeViewPrefs={mode:p.mode,ratio:Math.max(.1,Math.min(.9,p.ratio)),landscapeRatio:Number.isFinite(p.landscapeRatio)?Math.max(.1,Math.min(.9,p.landscapeRatio)):.5,syncIngredients:p.syncIngredients===true,autoCompleteIngredients:p.autoCompleteIngredients===true,keepScreenAwake:p.keepScreenAwake!==false,autoOpenLinkedRecipes:true,timerAlarmVolume:Number.isFinite(p.timerAlarmVolume)?Math.max(0,Math.min(1,p.timerAlarmVolume)):.8}}catch(e){}
function saveRecipeViewPrefs(){recipeViewPrefs.autoOpenLinkedRecipes=true;try{localStorage.setItem(RECIPE_VIEW_PREFS_KEY,JSON.stringify(recipeViewPrefs))}catch(e){/* Keep viewing available when preferences cannot be saved. */}}
// Recipe associations use existing content tokens, never schedule positions or progress state.
function syncIngredientHeading(text){
 const t=normalizeRecipeText(text).replace(/^#{1,6}\s+|\*\*/g,'').trim();
 if(/^\[[^\]\n]+\]$/.test(t))return t.slice(1,-1).replace(/^for\s+(?:the\s+)?/i,'').toLowerCase();
 if(/^(?:for\s+(?:the\s+)?)?(?:sauce|marinade|dressing|filling|topping)(?:\s+ingredients)?\s*:?$/i.test(t))return t.replace(/^for\s+(?:the\s+)?/i,'').replace(/\s+ingredients\s*:?$/i,'').replace(/:$/,'').toLowerCase();
 if(/^(?:#{1,6}\s+|\*\*)/.test(String(text))||(/^[A-Za-z][A-Za-z -]{1,55}:$/.test(t)))return t.replace(/:$/,'').toLowerCase();
 return '';
}
function recipeAssociationItems(meal){
 const items=cookingItemTokens(meal),counts=new Map();
 for(const item of [...items.ingredients,...items.steps])if(item.token){const base=item.token.replace(/#\d+$/,'');counts.set(base,(counts.get(base)||0)+1)}
 const unique=item=>item.token&&counts.get(item.token.replace(/#\d+$/,''))===1;
 return {ingredients:items.ingredients.filter(i=>!syncIngredientHeading(i.text)&&unique(i)),steps:items.steps.filter(i=>i.type==='step'&&cleanInstructionBlock(i).type!=='section'&&unique(i))};
}
// Viewer-only ordering: keep stored ingredient arrays and cooking tokens unchanged.
// Keep ingredient section headings attached to their original ingredients.
function recipeViewerIngredientOrder(meal,items){
 // Use the same effective associations as ingredient synchronization:
 // explicitly saved links override inferred links for each instruction step.
 const matches=recipeIngredientMatches(meal);
 const firstUse=new Map();
 let stepIndex=0;
 for(const item of items.steps){
  if(!item.token||cleanInstructionBlock(item).type==='section')continue;
  for(const token of matches.get(item.token)||[]){
   if(!firstUse.has(token))firstUse.set(token,stepIndex);
  }
  stepIndex++;
 }
 if(!firstUse.size)return items.ingredients;
 const sections=[{heading:null,entries:[]}];
 for(const item of items.ingredients){
  if(syncIngredientHeading(item.text))sections.push({heading:item,entries:[]});
  else sections[sections.length-1].entries.push(item);
 }
 const rank=section=>Math.min(Infinity,...section.entries.map(item=>firstUse.get(item.token)??Infinity));
 sections.forEach(section=>section.entries.sort((a,b)=>(firstUse.get(a.token)??Infinity)-(firstUse.get(b.token)??Infinity)));
 sections.sort((a,b)=>rank(a)-rank(b));
 return sections.flatMap(section=>section.heading?[section.heading,...section.entries]:section.entries);
}
function validRecipeIngredientLinks(meal,links=meal.ingredientStepLinks){
 const items=recipeAssociationItems(meal),ingredients=new Set(items.ingredients.map(i=>i.token)),steps=new Set(items.steps.map(i=>i.token));
 if(!Array.isArray(links))return [];
 const seen=new Set();return links.filter(link=>{
  if(!link||!steps.has(link.step)||seen.has(link.step)||!Array.isArray(link.ingredients)||!link.ingredients.every(t=>typeof t==='string'&&ingredients.has(t)))return false;
  seen.add(link.step);return true;
 }).map(link=>({step:link.step,ingredients:[...new Set(link.ingredients)]}));
}
function syncIngredientWords(text){
 const plural={onions:'onion',tomatoes:'tomato',potatoes:'potato',leaves:'leaf',chillies:'chili',chilies:'chili',chilli:'chili',chile:'chili',chiles:'chili',berries:'berry',inches:'inch',bunches:'bunch',halves:'half',radishes:'radish',cloves:'clove'};
 return (String(text).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().match(/[a-z]+/g)||[]).map(w=>plural[w]||(w.length>3&&w.endsWith('s')&&!/(ss|us|ous|is)$/.test(w)?w.slice(0,-1):w));
}
// Only matching text is normalized. Stored recipe text and cooking tokens are untouched.
const syncIngredientUnits=new Set(syncIngredientWords('cup tbsp tbs tsp tablespoon teaspoon gram kilogram kg g mg oz ounce lb lbs pound ml milliliter millilitre liter litre l fl fluid inch cm millimeter mm clove piece pinch dash sprig stalk bunch packet can jar x'));
const syncIngredientPrep=new Set(syncIngredientWords('a an the of about approximately optional divided medium large small fresh freshly finely roughly thinly thickly lightly gently chopped diced sliced minced grated crushed ground peeled seeded deseeded drained rinsed softened melted packed heaped level boneless skinless dried canned frozen whole halved quartered bruised trimmed smashed squeezed thick thin only'));
function syncIngredientMatchWords(value){
 const words=syncIngredientWords(value),typed=words.some(w=>['oil','sauce','pepper','sugar'].includes(w));
 return words.filter(w=>!syncIngredientPrep.has(w)||(typed&&['thin','thick'].includes(w)));
}
function syncIngredientNameWords(value){
 let text=normalizeRecipeText(ingredientLine(value)).replace(/\(s\)/gi,'s').split(/[,;]/)[0];
 // Trailing usage/quantity notes aren't part of a name (e.g. "salt to start").
 text=text.replace(/\b(?:to\s+(?:taste|start|finish|serve)|as\s+(?:needed|required|desired)|plus\s+(?:more|extra)|for\s+(?:serving|garnish|garnishing|topping)|or\s+(?:more|less)|cut\s+(?:into|in)|(?:sliced|diced|chopped|crushed)\s+into)\b.*$/i,'');
 const words=syncIngredientMatchWords(text);
 // Units are stripped from the quantity prefix, not from food names such as cloves.
 while(words.length>1&&syncIngredientUnits.has(words[0]))words.shift();
 return words;
}
function syncIngredientStepText(value){
 // Keep clause/conjunction boundaries so "rice, noodles" cannot become "rice noodles".
 return ' '+String(value).split(/[,;.!?\n]+/).map(part=>syncIngredientMatchWords(part).join(' ')).join(' | ')+' ';
}
function syncIngredientSpecificity(alias,text,index){
 const family=alias.split(' ').at(-1),after=text.slice(index+1+alias.length).trim().split(/\s+/)[0];
 if(['free','substitute','oil','sauce','powder','paste','extract','puree','salt','sugar','pepper','milk','broth','stock'].includes(after))return false;
 const qualifiers={oil:new Set(['olive','extra','virgin','neutral','sesame','toasted','annatto','chili','coconut','sunflower','peanut','vegetable','canola','avocado']),sauce:new Set(['thin','thick','light','dark','sweet','hot','chili','fish','soy','oyster','hoisin','tomato','barbecue','bbq']),sugar:new Set(['white','brown','light','dark','coconut','palm','rock','powdered','icing','caster','cane','granulated','raw','turbinado','demerara']),pepper:new Set(['black','white','red','green','yellow','orange','pink','bell','cayenne','chili','sichuan','szechuan']),broth:new Set(['beef','chicken','pork','turkey','duck','fish','seafood','vegetable','mushroom','bone']),stock:new Set(['beef','chicken','pork','turkey','duck','fish','seafood','vegetable','mushroom','bone']),noodle:new Set(['rice','egg','wheat','glass','soba','udon']),milk:new Set(['coconut','almond','oat','soy','rice','cashew','goat','evaporated','condensed'])};
 if(!qualifiers[family])return true;
 const before=text.slice(0,index).trim().split(/\s+/).at(-1);
 return !qualifiers[family].has(before);
}
function recipeIngredientMatches(meal){
 const all=cookingItemTokens(meal),items=recipeAssociationItems(meal),allowed=new Set(items.ingredients.map(i=>i.token));
 const ambiguous=new Set(['sauce','oil','mixture','ingredient','filling','topping','dressing','marinade','powder','fresh','ground']);
 const aliases=new Map(),groups=new Map(),groupCounts=new Map();let group='';
 const add=(alias,token,derived=false)=>{if(!aliases.has(alias))aliases.set(alias,{exact:new Set(),derived:new Set()});aliases.get(alias)[derived?'derived':'exact'].add(token)};
 for(const ingredient of all.ingredients){
  const heading=syncIngredientHeading(ingredient.text);if(heading){group=heading;groupCounts.set(group,(groupCounts.get(group)||0)+1);if(!groups.has(group))groups.set(group,[]);continue}
  if(!allowed.has(ingredient.token))continue;
  if(group)groups.get(group).push(ingredient.token);
  const words=syncIngredientNameWords(ingredient.text);
  if(!words.length)continue;
  const phrase=words.join(' ');if(phrase.length>=4&&!ambiguous.has(phrase))add(phrase,ingredient.token);
  // Prepared forms can share an unambiguous food name, but never erase oil/sauce/spice/sugar types.
  if(words.length>1&&['paste','puree','powder','extract'].includes(words.at(-1))&&!words.some(w=>['oil','sauce','pepper','sugar','chili','curry'].includes(w))){const base=words.slice(0,-1).join(' ');if(base.length>=4&&!ambiguous.has(base))add(base,ingredient.token,true)}
  // Generic food references are allowed only for constrained forms/cuts and a unique candidate.
  const meat=new Set(['beef','pork','chicken','lamb','turkey','duck']),cuts=new Set(['chuck','roast','steak','shank','brisket','rib','loin','tenderloin','breast','thigh','fillet','mince','bone','in','out','cubed']);
  if(words.length>1&&meat.has(words[0])&&words.slice(1).every(w=>cuts.has(w)))add(words[0],ingredient.token,true);
  if(words.length>1&&['broth','stock','noodle','pasta'].includes(words.at(-1)))add(words.at(-1),ingredient.token,true);
  // Short names must be explicit, familiar food names rather than measurement fragments.
  if(words.length===1&&['egg','ham','tea'].includes(phrase))add(phrase,ingredient.token);
 }
 const manual=new Map(validRecipeIngredientLinks(meal).map(l=>[l.step,l.ingredients]));const matches=new Map();
 for(const step of items.steps){
  if(manual.has(step.token)){matches.set(step.token,manual.get(step.token));continue}
  const text=syncIngredientStepText(cleanInstructionBlock(step).text),found=new Set();
  const spans=[];for(const [alias,choices] of aliases){const tokens=choices.exact.size?choices.exact:choices.derived;if(tokens.size!==1)continue;let from=0,index;while((index=text.indexOf(' '+alias+' ',from))!==-1){if(syncIngredientSpecificity(alias,text,index))spans.push({start:index+1,end:index+1+alias.length,token:[...tokens][0]});from=index+1}}
  const selected=[];for(const span of spans.sort((a,b)=>(b.end-b.start)-(a.end-a.start)))if(!selected.some(s=>span.start<s.end&&span.end>s.start)){selected.push(span);found.add(span.token)}
  const raw=' '+syncIngredientWords(cleanInstructionBlock(step).text).join(' ')+' ';
  for(const [heading,tokens] of groups){if(groupCounts.get(heading)!==1)continue;const name=syncIngredientWords(heading).join(' ');if(raw.includes(' '+name+' ingredient ')||raw.includes(' ingredient for '+name+' ')||raw.includes(' ingredient for the '+name+' '))tokens.forEach(t=>found.add(t))}
  matches.set(step.token,[...found]);
 }
 return matches;
}
function configureRecipeIngredientSync(v,meal,ingredientsPane,instructionsPane){
 v.syncCleanup?.();
 const enabled=recipeViewingMode()==='split'&&recipeViewPrefs.syncIngredients===true;
 v.sync.disabled=recipeViewingMode()!=='split';v.sync.checked=recipeViewPrefs.syncIngredients===true;
 if(v.linkEdit){v.syncToInstruction=null;v.cancelIngredientSync=null;return}
 const state=v.ingredientSyncState||(v.ingredientSyncState={suspended:false,lastStep:null,tokens:[]});
 const ingredientButtons=[...ingredientsPane.querySelectorAll('[data-cooking-token]')];
 const highlight=()=>ingredientButtons.forEach(b=>b.classList.toggle('recipe-sync-relevant',enabled&&state.tokens.includes(b.dataset.cookingToken)));
 highlight();v.syncToInstruction=null;if(!enabled){v.syncPinnedStep=null;state.tokens=[];state.lastStep=null;v.syncWasEnabled=false;return}
 const signature=JSON.stringify([meal.ingredients,meal.instructions,meal.ingredientStepLinks]);
 const matchesChanged=v.syncMatchSignature!==signature;if(matchesChanged){v.syncMatches=recipeIngredientMatches(meal);v.syncMatchSignature=signature;state.lastStep=null;state.tokens=[];highlight()}
 const steps=[...instructionsPane.querySelectorAll('[data-cooking-token]')];
 const events=new AbortController();let timer=null;
 const cancel=()=>{clearTimeout(timer);timer=null};v.cancelIngredientSync=cancel;
 const run=(force=false)=>{
  if(recipeViewer!==v||(!force&&state.suspended)||v.syncDividerDragging||v.syncGeometryHold)return;
  const box=instructionsPane.getBoundingClientRect(),anchor=box.top+box.height*.35;let active=steps.find(b=>b.dataset.cookingToken===v.syncPinnedStep)||null,distance=active?0:Infinity;const firstStep=steps[0]?.getBoundingClientRect();if(!active&&instructionsPane.scrollTop<2&&firstStep&&firstStep.top<box.bottom&&firstStep.bottom>box.top){active=steps[0];distance=0}
  for(const button of steps){if(v.syncPinnedStep&&active)break;const b=button.getBoundingClientRect();if(b.bottom<=box.top||b.top>=box.bottom)continue;const d=anchor<b.top?b.top-anchor:anchor>b.bottom?anchor-b.bottom:0;if(d<distance){distance=d;active=button}}
  const key=active?.dataset.cookingToken||null;if(key===state.lastStep)return;state.lastStep=key;state.tokens=v.syncMatches.get(key)||[];highlight();
  const relevant=ingredientButtons.filter(b=>state.tokens.includes(b.dataset.cookingToken));if(!relevant.length||state.suspended)return;
  const pane=ingredientsPane.getBoundingClientRect(),first=relevant[0].getBoundingClientRect(),last=relevant.at(-1).getBoundingClientRect();
  if(first.top>=pane.top+8&&last.bottom<=pane.bottom-8)return;
  ingredientsPane.scrollTo({top:Math.max(0,ingredientsPane.scrollTop+first.top-pane.top-12),behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
 };
 v.syncToInstruction=token=>{v.syncPinnedStep=token;state.lastStep=null;run(true)};
 const schedule=()=>{cancel();if(!state.suspended&&!v.syncDividerDragging&&!v.syncGeometryHold)timer=setTimeout(run,180)};
 const suspend=()=>{state.suspended=true;cancel();ingredientsPane.scrollTo({top:ingredientsPane.scrollTop,behavior:'instant'})};
 const resume=()=>{v.syncPinnedStep=null;state.suspended=false;state.lastStep=null;v.syncGeometryHold=false;schedule()};
 const on=(element,event,handler,options={})=>element.addEventListener(event,handler,{...options,signal:events.signal});
 on(instructionsPane,'scroll',schedule,{passive:true});
 for(const event of ['wheel','touchmove']){on(ingredientsPane,event,suspend,{passive:true});on(instructionsPane,event,resume,{passive:true})}
 const scrollKeys=new Set(['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' ']);
 on(ingredientsPane,'keydown',e=>{if(scrollKeys.has(e.key)&&e.target===ingredientsPane)suspend()});
 on(instructionsPane,'keydown',e=>{if(scrollKeys.has(e.key)&&e.target===instructionsPane)resume()});
 let pointer=null;on(ingredientsPane,'pointerdown',e=>{pointer={x:e.clientX,y:e.clientY};if(e.target===ingredientsPane)suspend()});
 on(ingredientsPane,'pointermove',e=>{if(pointer&&Math.hypot(e.clientX-pointer.x,e.clientY-pointer.y)>8)suspend()},{passive:true});
 for(const event of ['pointerup','pointercancel'])on(ingredientsPane,event,()=>{pointer=null});
 // A scrollbar drag is also a deliberate instruction scroll; ordinary button taps aren't.
 on(instructionsPane,'pointerdown',e=>{if(e.target===instructionsPane)resume()});
 ingredientsPane.tabIndex=0;instructionsPane.tabIndex=0;
 v.syncCleanup=()=>{cancel();events.abort();v.syncToInstruction=null};
 if(v.restoreTabScroll){cancel();v.syncWasEnabled=true;v.syncRequested=false;return}
 if(!v.syncWasEnabled||v.syncRequested){state.suspended=false;state.lastStep=null;v.syncGeometryHold=false;schedule()}else if(matchesChanged)schedule();
 v.syncWasEnabled=true;v.syncRequested=false;
}
function installRecipeIngredientLinkEditor(meal){
 const root=$('recipeIngredientLinks');if(!root)return;const body=root.querySelector('.settings-group-content');
 let draft=validRecipeIngredientLinks(meal),selected='';
 const draftMeal=()=>({...meal,ingredients:$('ingredients').value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean),instructions:$('recipeInstructions').value===instructionEditorText(meal.instructions)?meal.instructions:$('recipeInstructions').value});
 root.captureRecoveryDraft=()=>({links:JSON.parse(JSON.stringify(draft)),selectedStep:selected});root.getLinks=next=>validRecipeIngredientLinks(next||draftMeal(),draft);root.hasChanges=()=>JSON.stringify(root.getLinks())!==JSON.stringify(validRecipeIngredientLinks(meal));
 const render=()=>{
  const current=draftMeal(),items=recipeAssociationItems(current);draft=validRecipeIngredientLinks(current,draft);body.replaceChildren();
  const help=document.createElement('p');help.className='muted';help.textContent='Select a step to review or change its ingredients.';body.append(help);
  const label=document.createElement('label');label.textContent='Instruction step';const select=document.createElement('select');select.setAttribute('aria-label','Instruction step for ingredient links');
  for(const [n,item]of items.steps.entries()){const option=document.createElement('option');option.value=item.token;option.textContent=(n+1)+'. '+cleanInstructionBlock(item).text;select.append(option)}
  if(items.steps.some(i=>i.token===selected))select.value=selected;selected=select.value;select.onchange=()=>{selected=select.value;render()};label.append(select);body.append(label);
  if(!items.steps.length){const message=document.createElement('p');message.className='muted';message.textContent='Add distinct instruction steps and ingredients to create links.';body.append(message);return}
  const automatic=recipeIngredientMatches({...current,ingredientStepLinks:[]}).get(selected)||[],entry=draft.find(link=>link.step===selected),chosen=new Set(entry?entry.ingredients:automatic);
  const reset=document.createElement('button');reset.type='button';reset.className='meal-editor-text-action';reset.textContent='Reset to automatic';reset.hidden=!entry;reset.onclick=()=>{draft=draft.filter(link=>link.step!==selected);render();root.dispatchEvent(new Event('change',{bubbles:true}))};
  const list=document.createElement('div');list.className='recipe-link-choices';
  for(const ingredient of items.ingredients){const row=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=chosen.has(ingredient.token);input.onchange=()=>{if(input.checked)chosen.add(ingredient.token);else chosen.delete(ingredient.token);draft=draft.filter(link=>link.step!==selected);draft.push({step:selected,ingredients:[...chosen]});reset.hidden=false;root.dispatchEvent(new Event('change',{bubbles:true}))};row.append(input,document.createTextNode(ingredient.text));list.append(row)}body.append(list,reset);
 };
 root.ontoggle=()=>{if(root.open)render()};for(const id of ['ingredients','recipeInstructions'])$(id).addEventListener('change',()=>{if(root.open)render()});
}

function configureRecipeSplit(v,divider,panes){
 v.dividerGestureCleanup?.();v.resizeObserver?.disconnect();
 const events=new AbortController(),signal=events.signal,tab=v.activeTab;
 const landscape=()=>recipeViewingMode()==='split'&&matchMedia('(orientation: landscape) and (max-height: 600px) and (max-width: 1100px) and (pointer: coarse)').matches;
 const restoreSaved=v.restoreTabScroll,children=[...panes.querySelectorAll('.recipe-pane')];let drag=null,frame=0,changing=false,positions=tab.splitPlace||null,geometry='';
 const axis=()=>v.cover.classList.contains('recipe-landscape');
 const extent=()=>Math.max(1,(axis()?panes.clientWidth-divider.offsetWidth:panes.clientHeight-divider.offsetHeight));
 const snapshot=()=>children.map(pane=>{
  const box=pane.getBoundingClientRect(),nodes=[...pane.querySelectorAll('[data-cooking-token],h2,h3,.recipe-linked-link,.recipe-viewer-notes,.recipe-original')];
  const index=nodes.findIndex(node=>node.getBoundingClientRect().bottom>box.top+1),node=nodes[index],rect=node?.getBoundingClientRect();
  return {scroll:pane.scrollTop,index,token:node?.dataset.cookingToken||'',fraction:rect&&rect.top<box.top?Math.min(1,(box.top-rect.top)/Math.max(1,rect.height)):0,offset:rect?Math.max(0,rect.top-box.top):0};
 });
 const restore=saved=>{if(!saved)return;children.forEach((pane,i)=>{
  const place=saved[i];if(!place)return;const nodes=[...pane.querySelectorAll('[data-cooking-token],h2,h3,.recipe-linked-link,.recipe-viewer-notes,.recipe-original')],node=(place.token&&nodes.find(node=>node.dataset.cookingToken===place.token))||nodes[place.index];
  const box=pane.getBoundingClientRect(),rect=node?.getBoundingClientRect();pane.scrollTo({top:rect?pane.scrollTop+rect.top-box.top+place.fraction*rect.height-place.offset:place.scroll,behavior:'instant'});
 })};
 const remember=()=>{if(!changing&&recipeViewingMode()==='split'){positions=snapshot();tab.splitPlace=positions;tab.paneScroll=children.map(p=>p.scrollTop)}};
 v.rememberSplitViewport=remember;
 const freeze=()=>{v.syncGeometryHold=true;v.syncRequested=false;v.cancelIngredientSync?.();cancelRecipeAdvance(v)};
 const setRatio=(ratio,save=false)=>{
  const available=extent(),min=Math.min(axis()?180:96,available*(axis()?0.4:0.35));
  const clamped=Math.max(min/available,Math.min(1-min/available,ratio));
  const before=save?snapshot():null;if(save)freeze();
  v.cover.style.setProperty('--recipe-split-ratio',clamped);divider.setAttribute('aria-valuenow',String(Math.round(clamped*100)));
  if(save){const key=axis()?'landscapeRatio':'ratio';tab[key]=clamped;recipeViewPrefs[key]=clamped;saveRecipeViewPrefs();restore(before);remember()}
 };
 const end=()=>{const old=drag;drag=null;v.syncDividerDragging=false;if(old?.source==='pointer'&&divider.hasPointerCapture(old.id))divider.releasePointerCapture(old.id)};
 const layout=()=>{v.cover.classList.toggle('recipe-landscape',landscape());divider.setAttribute('aria-orientation',axis()?'vertical':'horizontal');setRatio(recipeSplitRatio())};
 const signature=()=>[landscape(),panes.clientWidth,panes.clientHeight,innerWidth,innerHeight].join(':');
 const reflow=()=>{
  if(recipeViewer!==v)return;const next=signature();if(next===geometry)return;
  end();v.cancelTabDrag?.();freeze();const saved=positions||snapshot();changing=true;cancelAnimationFrame(frame);layout();geometry=signature();
  if(recipeViewingMode()!=='split'){changing=false;return}
  // Keep semantic anchors through wrapping and Android viewport-bar settling.
  frame=requestAnimationFrame(()=>{restore(saved);frame=requestAnimationFrame(()=>{restore(saved);changing=false;remember()})});
 };
 layout();geometry=signature();
 frame=requestAnimationFrame(()=>{if(restoreSaved&&positions&&recipeViewingMode()==='split')restore(positions);remember()});
 for(const pane of children)pane.addEventListener('scroll',remember,{signal,passive:true});
 window.addEventListener('resize',reflow,{signal});window.visualViewport?.addEventListener('resize',reflow,{signal});
 if(typeof ResizeObserver==='function'){v.resizeObserver=new ResizeObserver(reflow);v.resizeObserver.observe(panes)}
 const begin=(x,y,source,id)=>{freeze();v.syncDividerDragging=true;const box=divider.getBoundingClientRect();drag={source,id,offset:axis()?x-box.left:y-box.top,landscape:axis()}};
 const move=(x,y)=>{if(!drag)return;if(drag.landscape!==axis()){end();return}const box=panes.getBoundingClientRect();setRatio(((axis()?x-box.left:y-box.top)-drag.offset)/extent(),true)};
 v.dividerGestureCleanup=()=>{end();events.abort();cancelAnimationFrame(frame);v.rememberSplitViewport=null};
 divider.addEventListener('touchstart',e=>{if(e.cancelable)e.preventDefault();e.stopPropagation();if(e.touches.length!==1||drag){end();return}const t=e.changedTouches[0];begin(t.clientX,t.clientY,'touch',t.identifier)},{signal,passive:false});
 divider.addEventListener('touchmove',e=>{if(drag?.source!=='touch')return;const t=[...e.changedTouches].find(t=>t.identifier===drag.id);if(!t)return;if(e.cancelable)e.preventDefault();e.stopPropagation();move(t.clientX,t.clientY)},{signal,passive:false});
 divider.addEventListener('touchend',e=>{if(drag?.source!=='touch'||![...e.changedTouches].some(t=>t.identifier===drag.id))return;if(e.cancelable)e.preventDefault();e.stopPropagation();end();remember()},{signal,passive:false});
 divider.addEventListener('touchcancel',()=>{if(drag?.source==='touch')end()},{signal});
 divider.onpointerdown=e=>{if(e.pointerType==='touch'||e.button!==0)return;e.preventDefault();e.stopPropagation();begin(e.clientX,e.clientY,'pointer',e.pointerId);divider.setPointerCapture(e.pointerId)};
 divider.onpointermove=e=>{if(drag?.source!=='pointer'||drag.id!==e.pointerId)return;e.preventDefault();e.stopPropagation();move(e.clientX,e.clientY)};
 divider.onpointerup=divider.onpointercancel=e=>{if(drag?.source==='pointer'&&drag.id===e.pointerId){e.preventDefault();e.stopPropagation();end();remember()}};
 divider.onlostpointercapture=e=>{if(e.target===divider&&drag?.source==='pointer'&&drag.id===e.pointerId)end()};divider.onclick=e=>{e.preventDefault();e.stopPropagation()};
 window.addEventListener('blur',end,{signal});document.addEventListener('visibilitychange',()=>{if(document.hidden)end()},{signal});
 divider.onkeydown=e=>{const delta=(axis()?{ArrowLeft:-.05,ArrowRight:.05,Home:-1,End:1}:{ArrowUp:-.05,ArrowDown:.05,Home:-1,End:1})[e.key];if(delta!==undefined){e.preventDefault();setRatio(recipeSplitRatio()+delta,true)}};
}

let recipeViewer=null,recipeViewerHistoryClosing=false;
// Keep content identity separate from schedule identity. A viewer deck owns its
// temporary (unscheduled) states; persisted progress still uses the existing keys.
function recipeViewingMode(){return recipeViewer?.activeTab?.mode||recipeViewPrefs.mode}
function recipeSplitRatio(){return recipeViewer?.cover.classList.contains('recipe-landscape')?(recipeViewer.activeTab?.landscapeRatio??recipeViewPrefs.landscapeRatio??.5):(recipeViewer?.activeTab?.ratio??recipeViewPrefs.ratio)}
function recipePlanEntries(planId){
 const plan=mealPlans.find(p=>String(p.id)===String(planId));if(!plan)return [];
 return getDisplayedWeekdayMealsForPlan(String(plan.id)===String(activePlanId)?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan);
}
// A verified day/plan origin is separate from a definite cooking occurrence.
function recipeScheduleOrigin(meal,context){
 if(!context||!recipePlanEntries(context.planId).some(e=>e.day===context.day&&String(e.meal.id)===String(meal.id)))return null;
 return {planId:String(context.planId),day:context.day};
}
function definiteRecipeContext(context){
 if(!context)return null;
 const matches=recipePlanEntries(context.planId).filter(e=>e.day===context.day&&String(e.meal.id)===String(context.mealId)&&String(e.linkedTo||'')===String(context.parentId||'')&&e.cat===context.cat);
 return matches.length===1?cookingContext(context.planId,context.day,matches[0].cat,matches[0].meal,matches[0].linkedTo):null;
}
function linkedRecipeContext(source,child){
 const context=definiteRecipeContext(source.context);if(!context)return null;
 const candidates=recipePlanEntries(context.planId).filter(e=>e.day===context.day&&String(e.meal.id)===String(child.id));
 // Prefer the exact linked parent. An independently scheduled recipe on this
 // same day is also definite; a different parent's linked occurrence is not.
 const owned=candidates.filter(e=>String(e.linkedTo||'')===String(source.mealId));
 const independent=candidates.filter(e=>!e.linkedTo||e.scheduledSlot),found=owned.length?owned:independent;
 return found.length===1?cookingContext(context.planId,context.day,found[0].cat,child,found[0].linkedTo):null;
}
function viewerRecipeContext(meal,context){
 const direct=definiteRecipeContext(context);if(direct||!context?.parentId)return direct;
 // Existing rotation-side actions can supply a parent even when the child was
 // already scheduled independently. Resolve that caller exactly like a tab link.
 const parents=recipePlanEntries(context.planId).filter(e=>e.day===context.day&&String(e.meal.id)===String(context.parentId)&&(e.meal.linkedMealIds||[]).some(id=>String(id)===String(meal.id)));
 if(parents.length!==1)return null;const parent=parents[0];
 return linkedRecipeContext({mealId:String(parent.meal.id),context:cookingContext(context.planId,context.day,parent.cat,parent.meal,parent.linkedTo)},meal);
}
function recipeTabKey(meal,context){return context?'occurrence:'+scaleOccurrenceKey(context):'preview:'+String(meal.id)}
function createRecipeTab(meal,context,mode=recipeViewPrefs.mode,ratio=recipeViewPrefs.ratio){
 return {key:recipeTabKey(meal,context),mealId:String(meal.id),context,mode,ratio,landscapeRatio:recipeViewPrefs.landscapeRatio??.5,previewProgress:{ingredients:[],steps:[]},previewScale:1,coverScroll:0,paneScroll:[0,0],recipeContent:{ingredients:meal.ingredients,instructions:meal.instructions}};
}
function installRecipeViewerTabs(view,meal,context,saved=null){
 const initial=createRecipeTab(meal,viewerRecipeContext(meal,context));
 view.tabs=[initial];view.anchorTab=initial;view.tabCache=new Map([[initial.key,initial]]);view.activeTab=initial;
 // Existing viewer logic continues to read/write these fields on the active tab.
 const fields=['mealId','context','previewProgress','previewScale','ingredientSyncState','syncMatches','syncMatchSignature','syncWasEnabled','syncRequested','syncPinnedStep','syncGeometryHold','advanceSpace','linkIngredientTailSpace','linkTailSpace','linkEdit','linkNotice','linkLayoutTransition','importMessage'];
 for(const field of fields){delete view[field];Object.defineProperty(view,field,{get:()=>view.activeTab[field],set:value=>{view.activeTab[field]=value},configurable:true})}
 const strip=document.createElement('div');strip.className='recipe-tab-strip';strip.setAttribute('role','tablist');strip.setAttribute('aria-label','Open recipes');view.content.before(strip);view.tabStrip=strip;installRecipeTabReordering(view);if(typeof ResizeObserver==='function'){let width=-1;view.tabResizeObserver=new ResizeObserver(()=>{const next=strip.clientWidth;if(next===width)return;width=next;layoutRecipeTabNames(view,true)});view.tabResizeObserver.observe(strip)}view.content.id='recipeViewerPanel';view.content.setAttribute('role','tabpanel');
 if(saved){
  const remapped=new Map();for(const tab of saved.cache.values()){
   const current=meals.find(m=>String(m.id)===tab.mealId);if(!current)continue;
   tab.previewProgress=compatiblePreviewProgress(tab.previewProgress,tab.recipeContent,current);tab.recipeContent={ingredients:current.ingredients,instructions:current.instructions};
   tab.context=definiteRecipeContext(tab.context);tab.key=tab.context?recipeTabKey(current,tab.context):(tab.previewKey||recipeTabKey(current,null));remapped.set(tab.key,tab);
  }
  const anchor=remapped.get(saved.anchor.key)||initial;
  view.tabCache=remapped;view.tabCache.set(anchor.key,anchor);view.anchorTab=anchor;view.tabs=saved.tabs.filter(t=>remapped.get(t.key)===t);if(!view.tabs.includes(anchor))view.tabs.unshift(anchor);view.activeTab=view.tabs.find(t=>t===saved.active)||anchor;view.restoreTabScroll=true;view.syncGeometryHold=true;
 }else{
  for(const id of meal.linkedMealIds||[]){const child=meals.find(m=>String(m.id)===String(id));if(child)openLinkedRecipeTab(child,view.anchorTab,false)}
 }
}
function captureRecipeTab(view){
 const tab=view.activeTab;if(!tab)return;
 if(recipeViewingMode()==='full')tab.coverScroll=view.cover.scrollTop;else{view.rememberSplitViewport?.();tab.paneScroll=[...view.content.querySelectorAll('.recipe-pane')].map(p=>p.scrollTop)}tab.focusToken=document.activeElement?.dataset.cookingToken;
 for(const pane of view.content.querySelectorAll('.recipe-pane'))pane.scrollTo({top:pane.scrollTop,behavior:'instant'});
}
function snapshotRecipeTabs(view){view.cancelTabDrag?.();captureRecipeTab(view);return {tabs:[...view.tabs],cache:new Map(view.tabCache),active:view.activeTab,anchor:view.anchorTab,scheduleOrigin:view.scheduleOrigin}}
function switchRecipeTab(tab){
 const view=recipeViewer;if(!view||tab===view.activeTab)return;view.cancelTabDrag?.();
 if(view.linkEdit){recipeLinkMessage(view,'Save or cancel the current ingredient links before switching recipe tabs.');return}
 captureRecipeTab(view);cancelRecipeAdvance(view);view.importController?.abort();view.resizeObserver?.disconnect();view.syncCleanup?.();view.guidedCleanup?.();view.scaleCleanup?.();clearRecipeLinkGestures(view);
 view.activeTab=tab;view.restoreTabScroll=true;view.syncGeometryHold=true;view.syncDividerDragging=false;view.suppressLinkGestureClick=false;
 view.cookingSettings.hidden=true;view.settings.setAttribute('aria-expanded','false');
 renderRecipeViewer();const meal=meals.find(m=>String(m.id)===tab.mealId);if(meal)enrichViewedRecipe(meal);
}
function openLinkedRecipeTab(child,source=recipeViewer?.activeTab,activate=true){
 const view=recipeViewer;if(!view||!source||!meals.some(m=>String(m.id)===String(child?.id)))return;view.cancelTabDrag?.();
 if(view.linkEdit){recipeLinkMessage(view,'Save or cancel the current ingredient links before opening another recipe tab.');return}
 // A link back to the anchor always selects the definite anchor of this deck.
 if(String(child.id)===view.anchorTab.mealId){if(activate)switchRecipeTab(view.anchorTab);return}
 const context=linkedRecipeContext(source,child),previewKey='preview:'+JSON.stringify([source.context?cookingOccurrenceKey(source.context):view.anchorTab.key,String(child.id)]),key=context?recipeTabKey(child,context):previewKey;
 let tab=view.tabCache.get(key);if(!tab){tab=createRecipeTab(child,context);tab.key=key;tab.previewKey=previewKey;view.tabCache.set(key,tab)}
 if(!view.tabs.includes(tab))view.tabs.push(tab);
 if(activate){if(tab===view.activeTab)renderRecipeTabs(view);else switchRecipeTab(tab)}
}
function addViewerRecipe(meal,context=null){
 const view=recipeViewer;if(!view||!meal)return null;
 const already=view.tabs.find(tab=>tab.mealId===String(meal.id));if(already)return already;
 const definite=viewerRecipeContext(meal,context),key=recipeTabKey(meal,definite);
 let tab=view.tabCache.get(key)||[...view.tabCache.values()].find(t=>t.mealId===String(meal.id)&&(definite?t.context&&cookingOccurrenceKey(t.context)===cookingOccurrenceKey(definite):!t.context));
 if(!tab){tab=createRecipeTab(meal,definite);view.tabCache.set(tab.key,tab)}view.tabs.push(tab);return tab;
}
// Add to the existing deck, retaining occurrence-specific state and closed-tab caches.
// A checklist selection limits automatic links to the explicitly confirmed deck.
function addViewerRecipes(entries,selection=null,linkedSources=new Map()){
 const view=recipeViewer;if(!view)return false;
 if(view.linkEdit){recipeLinkMessage(view,'Save or cancel the current ingredient links before opening another recipe tab.');return false}
 captureRecipeTab(view);const active=view.activeTab;
 if(selection)view.tabs=view.tabs.filter(tab=>tab===view.anchorTab||selection.has(tab.mealId));
 for(const {meal,context}of entries){
  const parent=linkedSources.get(String(meal.id)),sourceTab=parent&&view.tabs.find(tab=>tab.mealId===parent);
  if(sourceTab&&!view.tabs.some(tab=>tab.mealId===String(meal.id)))openLinkedRecipeTab(meal,sourceTab,false);
  const source=addViewerRecipe(meal,context);if(!source||selection)continue;
  for(const id of meal.linkedMealIds||[]){if(view.tabs.some(t=>t.mealId===String(id)))continue;const child=meals.find(m=>String(m.id)===String(id));if(child)openLinkedRecipeTab(child,source,false)}
 }
 if(!view.tabs.includes(active))switchRecipeTab(view.anchorTab);else renderRecipeTabs(view);return true;
}
function openViewerRecipes(){
 const view=recipeViewer;if(!view||view.openRecipesDialog)return;
 if(view.linkEdit){recipeLinkMessage(view,'Save or cancel the current ingredient links before opening another recipe tab.');return}
 // Only a verified originating day/plan is used; collection previews never guess.
 const anchor=meals.find(m=>String(m.id)===view.anchorTab.mealId),origin=anchor&&recipeScheduleOrigin(anchor,view.scheduleOrigin);
 const scheduled=origin?recipePlanEntries(origin.planId).filter(e=>e.day===origin.day):[],unique=[...new Map(scheduled.map(e=>[String(e.meal.id),e.meal])).values()];
 function contextFor(meal){if(!origin)return null;const matches=scheduled.filter(e=>String(e.meal.id)===String(meal.id));if(matches.length!==1)return null;const item=matches[0];return cookingContext(origin.planId,item.day,item.cat,item.meal,item.linkedTo)}
 const primary=view.anchorTab.mealId,open=new Set(view.tabs.map(tab=>tab.mealId)),selected=new Set([...open,...unique.map(meal=>String(meal.id))]),listed=new Set([...unique.map(meal=>String(meal.id)),...open]),excluded=new Set(),linkedSources=new Map();
 // Reflect linked opening in the draft checkboxes, never in the live viewer.
 // Explicit unchecking wins over automatic linking for this confirmation.
 function selectRecipe(id,scope=null){selected.add(id);listed.add(id);const meal=meals.find(m=>String(m.id)===id);if(!meal)return;for(const raw of meal.linkedMealIds||[]){const child=String(raw);if((scope&&!scope.has(child))||excluded.has(child)||selected.has(child)||!meals.some(m=>String(m.id)===child))continue;selected.add(child);listed.add(child);linkedSources.set(child,id)}}
 for(const meal of unique)selectRecipe(String(meal.id));
 const cover=document.createElement('div');cover.className='recipe-timer-dialog recipe-open-dialog';cover.setAttribute('role','dialog');cover.setAttribute('aria-modal','true');cover.setAttribute('aria-label','Open Recipes');
 const panel=document.createElement('div'),header=document.createElement('div');header.className='recipe-open-heading';const title=document.createElement('strong');title.textContent='Open Recipes';const close=document.createElement('button');close.type='button';close.className='recipe-timer-icon';setRecipeToolbarIcon(close,'close','Close open recipes');header.append(title,close);
 const search=document.createElement('input');search.type='search';search.placeholder='Search recipes';search.setAttribute('aria-label','Search all recipes');
 const controls=document.createElement('div');controls.className='recipe-open-selection';const list=document.createElement('div');list.className='recipe-open-list';let visible=[];
 function toggle(id,checked){if(checked){excluded.delete(id);selectRecipe(id)}else if(id!==primary){selected.delete(id);excluded.add(id)}display()}
 for(const [label,path,checked]of [['Select all','m7 12 3 3 7-7',true],['Deselect all','M8 12h8',false]]){const button=document.createElement('button');button.type='button';button.className='recipe-timer-icon';button.title=label;button.setAttribute('aria-label',label);button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="'+path+'"/></svg>';button.onclick=()=>{const scope=new Set(visible.map(meal=>String(meal.id)));for(const meal of visible){const id=String(meal.id);if(checked){excluded.delete(id);selectRecipe(id,scope)}else if(id!==primary){selected.delete(id);excluded.add(id)}}display()};controls.append(button)}
 function display(){
  const scroll=list.scrollTop,focusId=document.activeElement?.closest('.recipe-open-choice')?.dataset.mealId,query=search.value.trim(),collection=[...new Map([...cats.flatMap(cat=>masterRecipeOrder(cat)),...meals].map(m=>[String(m.id),m])).values()];
  visible=query?collection.filter(meal=>mealMatchesSearch(meal,query)):[...listed].map(id=>meals.find(meal=>String(meal.id)===id)).filter(Boolean);controls.hidden=visible.length<2;list.replaceChildren();
  for(const meal of visible){const id=String(meal.id),row=document.createElement('label');row.className='recipe-open-choice';row.dataset.mealId=id;const check=document.createElement('input');check.type='checkbox';check.className='check';check.checked=selected.has(id);check.disabled=id===primary;check.setAttribute('aria-label','Open '+(meal.name||'Untitled meal'));check.onchange=()=>toggle(id,check.checked);const text=document.createElement('span');text.textContent=meal.name||'Untitled meal';if(id===primary){const hint=document.createElement('small');hint.textContent='Primary recipe · stays open';text.append(hint)}row.append(check,text);list.append(row)}
  if(!visible.length){const empty=document.createElement('p');empty.className='muted';empty.textContent='No matching recipes.';list.append(empty)}list.scrollTop=scroll;if(focusId)[...list.querySelectorAll('.recipe-open-choice')].find(row=>row.dataset.mealId===focusId)?.querySelector('input')?.focus({preventScroll:true});
 }
 const actions=document.createElement('div');actions.className='meal-unified-actions';const confirm=document.createElement('button');confirm.type='button';setIconButton(confirm,'save','Open selected recipes');const cancel=document.createElement('button');cancel.type='button';setIconButton(cancel,'cancel','Cancel open recipes');actions.append(confirm,cancel);panel.append(header,search,controls,list,actions);cover.append(panel);
 const focused=document.activeElement,inert=[...document.body.children].map(el=>[el,el.inert]);for(const [el]of inert)el.inert=true;
 let closed=false;function dismiss(){if(closed)return;closed=true;if(view.openRecipesDialog===dismiss)view.openRecipesDialog=null;cover.remove();for(const [el,was]of inert)if(el.isConnected)el.inert=was;if(focused?.isConnected)focused.focus({preventScroll:true})}
 view.openRecipesDialog=dismiss;close.onclick=cancel.onclick=dismiss;confirm.onclick=()=>{if(recipeViewer!==view){dismiss();return}selected.add(primary);const entries=[...selected].map(id=>meals.find(meal=>String(meal.id)===id)).filter(Boolean).map(meal=>({meal,context:contextFor(meal)}));if(addViewerRecipes(entries,selected,linkedSources))dismiss()};search.oninput=()=>{list.scrollTop=0;display()};cover.onclick=e=>{if(e.target===cover)dismiss()};cover.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();dismiss()}if(e.key==='Tab'){const buttons=[...panel.querySelectorAll('button:not([disabled]),input:not([disabled])')].filter(el=>el.getClientRects().length),first=buttons[0],last=buttons.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}};document.body.append(cover);display();close.focus({preventScroll:true});
}

function closeLinkedRecipeTab(tab){
 const view=recipeViewer;if(!view||tab===view.anchorTab)return;view.cancelTabDrag?.();
 if(view.linkEdit){recipeLinkMessage(view,'Save or cancel the current ingredient links before closing a recipe tab.');return}
 if(tab===view.activeTab)switchRecipeTab(view.anchorTab);
 view.tabs=view.tabs.filter(t=>t!==tab);renderRecipeTabs(view);(view.tabStrip.hidden?view.close:view.tabStrip.querySelector('[role="tab"][aria-selected="true"]'))?.focus({preventScroll:true});
 // Cache the closed tab until the whole viewer closes, including its preview progress.
}
// Reordering changes this viewer's tab array/DOM only, never recipe relationships.
function installRecipeTabReordering(view){
 const strip=view.tabStrip,events=new AbortController(),signal=events.signal;let gesture=null;
 const listen=(target,name,fn,options={})=>target.addEventListener(name,fn,{...options,signal});
 const order=()=>{const left=strip.scrollLeft,focus=document.activeElement;view.tabs.forEach((tab,index)=>{const node=[...strip.children].find(el=>el.dataset.recipeTabKey===tab.key);if(!node)return;if(gesture?.phase==='drag')node.style.order=index;else{node.style.removeProperty('order');strip.append(node)}});strip.scrollLeft=left;if(strip.contains(focus))focus.focus({preventScroll:true})};
 const end=(cancel=false)=>{
  const drag=gesture;if(!drag)return;gesture=null;clearTimeout(drag.timer);cancelAnimationFrame(drag.frame);
  if(drag.phase==='drag'){
   if(cancel)view.tabs=drag.before;order();
   drag.item.classList.remove('recipe-tab-dragging');drag.ghost?.remove();view.tabDragging=false;layoutRecipeTabNames(view,false);
  }
  if(drag.phase!=='pending')view.suppressRecipeTabClick=true;
  if(drag.source==='pointer'&&strip.hasPointerCapture(drag.pointer))strip.releasePointerCapture(drag.pointer);
 };
 view.cancelTabDrag=()=>end(true);view.tabDragCleanup=()=>{end(true);events.abort()};
 const place=drag=>{
  const at=view.tabs.indexOf(drag.tab),direction=drag.direction;if(!direction)return;
  const next=view.tabs[at+(direction>0?1:-1)];if(!next)return;
  const neighbor=[...strip.children].find(el=>el.dataset.recipeTabKey===next.key);if(!neighbor)return;const box=neighbor.getBoundingClientRect();
  if(direction>0?drag.x>box.left+box.width/2:drag.x<box.left+box.width/2){view.tabs.splice(at,1);view.tabs.splice(at+(direction>0?1:-1),0,drag.tab);order()}
 };
 const frame=()=>{
  const drag=gesture;if(!drag||drag.phase!=='drag')return;
  const box=strip.getBoundingClientRect(),edge=28;
  const velocity=drag.x<box.left+edge?-Math.min(12,(box.left+edge-drag.x)/2):drag.x>box.right-edge?Math.min(12,(drag.x-box.right+edge)/2):0;
  if(velocity){strip.scrollLeft+=velocity;drag.direction=Math.sign(velocity)}
  drag.ghost.style.left=Math.max(box.left,Math.min(box.right-drag.width,drag.x-drag.offset))+'px';
  place(drag);drag.frame=requestAnimationFrame(frame);
 };
 const begin=(target,x,y,source,pointer)=>{
  view.suppressRecipeTabClick=false;
  const button=target.closest('button'),item=target.closest('.recipe-tab'),tab=view.tabs.find(t=>t.key===item?.dataset.recipeTabKey);
  const drag={tab,item,button,source,pointer,x,y,startX:x,startY:y,previousX:x,scroll:strip.scrollLeft,phase:'pending',before:[...view.tabs]};gesture=drag;
  if(!tab)return; // Empty strip/gaps still accept horizontal swipes.
  drag.timer=setTimeout(()=>{
   if(gesture!==drag||!item.isConnected)return;
   if(button?.classList.contains('recipe-tab-close')){drag.phase='held';view.suppressRecipeTabClick=true;return}
   if(view.linkEdit){drag.phase='held';end();recipeLinkMessage(view,'Save or cancel ingredient links before reordering recipe tabs.');return}
   cancelRecipeAdvance(view);drag.phase='drag';view.tabDragging=true;view.suppressRecipeTabClick=true;
   const box=item.getBoundingClientRect();drag.width=box.width;drag.offset=drag.startX-box.left;drag.ghost=item.cloneNode(true);drag.ghost.classList.add('recipe-tab-drag-preview');drag.ghost.setAttribute('aria-hidden','true');drag.ghost.inert=true;
   for(const node of drag.ghost.querySelectorAll('[id]'))node.removeAttribute('id');drag.ghost.removeAttribute('data-recipe-tab-key');
   drag.ghost.style.cssText='position:fixed;top:'+box.top+'px;left:'+box.left+'px;width:'+box.width+'px;height:'+box.height+'px;z-index:8;pointer-events:none';view.cover.append(drag.ghost);item.classList.add('recipe-tab-dragging');
   if(source==='pointer')strip.setPointerCapture(pointer);drag.frame=requestAnimationFrame(frame);
  },550);
 };
 const move=(x,y)=>{
  const drag=gesture;if(!drag)return;const dx=x-drag.startX,dy=y-drag.startY;
  if(drag.phase==='pending'&&Math.hypot(dx,dy)>10){clearTimeout(drag.timer);drag.phase='scroll';if(drag.source==='pointer')strip.setPointerCapture(drag.pointer)}
  if(drag.phase==='scroll'){strip.scrollLeft=drag.scroll-dx;view.suppressRecipeTabClick=true}
  if(drag.phase==='drag'){const change=x-drag.previousX;if(change)drag.direction=Math.sign(change);drag.x=x;drag.y=y;view.suppressRecipeTabClick=true}
  drag.previousX=x;
 };
 // Own the whole touch stream from its start, including tab padding and X buttons.
 // Do not mix it with Android's implicit pointer capture or compatibility clicks.
 listen(strip,'touchstart',e=>{
  if(e.cancelable)e.preventDefault();
  if(e.touches.length!==1||gesture){end(true);return}
  const t=e.changedTouches[0];begin(e.target,t.clientX,t.clientY,'touch',t.identifier);
 },{passive:false});
 listen(strip,'touchmove',e=>{
  const drag=gesture;if(drag?.source!=='touch')return;
  const t=[...e.changedTouches].find(t=>t.identifier===drag.pointer);if(!t)return;
  if(e.cancelable)e.preventDefault();move(t.clientX,t.clientY);
 },{passive:false});
 listen(strip,'touchend',e=>{
  const drag=gesture;if(drag?.source!=='touch'||![...e.changedTouches].some(t=>t.identifier===drag.pointer))return;
  if(e.cancelable)e.preventDefault();const tap=drag.phase==='pending'?drag.button:null;end();
  if(tap?.isConnected){view.suppressRecipeTabClick=false;tap.focus({preventScroll:true});tap.click()}
 },{passive:false});
 listen(strip,'touchcancel',e=>{if(gesture?.source==='touch'){if(e.cancelable)e.preventDefault();end(true)}},{passive:false});
 // Mouse/pen keep pointer capture; touch is handled once by the listeners above.
 listen(strip,'pointerdown',e=>{if(e.pointerType==='touch'||e.button!==0)return;if(gesture){end(true);return}begin(e.target,e.clientX,e.clientY,'pointer',e.pointerId)});
 listen(document,'pointermove',e=>{if(gesture?.source!=='pointer'||e.pointerId!==gesture.pointer)return;move(e.clientX,e.clientY);if(gesture?.phase!=='pending'&&e.cancelable)e.preventDefault()},{passive:false});
 listen(document,'pointerup',e=>{if(gesture?.source==='pointer'&&e.pointerId===gesture.pointer)end()});
 listen(document,'pointercancel',e=>{if(gesture?.source==='pointer'&&e.pointerId===gesture.pointer)end(true)});
 listen(strip,'lostpointercapture',e=>{if(e.target===strip&&gesture?.source==='pointer'&&e.pointerId===gesture.pointer)end(true)});
 listen(window,'blur',()=>end(true));listen(document,'visibilitychange',()=>{if(document.hidden)end(true)});
 listen(strip,'click',e=>{if(view.suppressRecipeTabClick){view.suppressRecipeTabClick=false;e.preventDefault();e.stopImmediatePropagation()}},{capture:true});
 listen(strip,'contextmenu',e=>e.preventDefault());
 listen(strip,'keydown',e=>{view.suppressRecipeTabClick=false;if(e.key==='Escape'&&gesture){e.preventDefault();e.stopPropagation();end(true)}});
}

function layoutRecipeTabNames(view,reveal=false){
 const strip=view.tabStrip;if(!strip||strip.hidden||!strip.clientWidth||view.tabDragging)return;
 const left=strip.scrollLeft,buttons=[...strip.querySelectorAll('[role="tab"]')];
 // Measure full labels without truncation, so abbreviation is based on available
 // space rather than arbitrary title lengths or the already abbreviated row.
 strip.classList.remove('recipe-tabs-abbreviated');
 for(const button of buttons)button.textContent=button.dataset.fullName;
 const abbreviate=strip.scrollWidth>strip.clientWidth+1;
 strip.classList.toggle('recipe-tabs-abbreviated',abbreviate);
 strip.style.setProperty('--recipe-tabs-width',strip.clientWidth+'px');
 if(abbreviate)for(const button of buttons){const words=button.dataset.fullName.trim().split(/\s+/);button.textContent=words.length>1?words[0]+' '+Array.from(words[1])[0]+'…':button.dataset.fullName}
 strip.scrollLeft=left;
 const selected=strip.querySelector('.active');if(reveal&&selected){const box=selected.getBoundingClientRect(),pane=strip.getBoundingClientRect();if(box.left<pane.left)strip.scrollLeft+=box.left-pane.left;else if(box.right>pane.right)strip.scrollLeft+=box.right-pane.right}
}

function renderRecipeTabs(view){
 const strip=view.tabStrip;if(!strip)return;view.cancelTabDrag?.();const left=strip.scrollLeft,focusKey=document.activeElement?.dataset.recipeTab,wasHidden=strip.hidden,scroll=view.cover.scrollTop,panes=[...view.content.querySelectorAll('.recipe-pane')],paneScroll=panes.map(p=>p.scrollTop);
 strip.replaceChildren();strip.hidden=view.tabs.length<2;
 view.tabs.forEach((tab,index)=>{
  const meal=meals.find(m=>String(m.id)===tab.mealId),name=meal?.name||'Recipe unavailable',item=document.createElement('div');item.className='recipe-tab';item.dataset.recipeTabKey=tab.key;item.classList.toggle('recipe-tab-anchor',tab===view.anchorTab);item.classList.toggle('active',tab===view.activeTab);
  const select=document.createElement('button');select.type='button';select.setAttribute('role','tab');select.setAttribute('aria-selected',String(tab===view.activeTab));select.setAttribute('aria-controls','recipeViewerPanel');select.tabIndex=tab===view.activeTab?0:-1;select.id='recipeViewerTab'+index;select.dataset.recipeTab=tab.key;select.textContent=name;select.dataset.fullName=name;select.title=name;select.setAttribute('aria-label',name);
  select.onclick=()=>switchRecipeTab(tab);select.onkeydown=e=>{const index=view.tabs.indexOf(tab),offset={ArrowLeft:-1,ArrowRight:1,Home:-index,End:view.tabs.length-1-index}[e.key];if(offset===undefined)return;e.preventDefault();const next=view.tabs[(index+offset+view.tabs.length)%view.tabs.length];switchRecipeTab(next);[...strip.querySelectorAll('[role="tab"]')].find(b=>b.dataset.recipeTab===next.key)?.focus({preventScroll:true})};item.append(select);
  if(tab!==view.anchorTab){const close=document.createElement('button');close.type='button';close.className='recipe-tab-close';setRecipeToolbarIcon(close,'close','Close '+name+' tab');close.onclick=()=>closeLinkedRecipeTab(tab);item.append(close)}
  strip.append(item);if(tab===view.activeTab)view.content.setAttribute('aria-labelledby',select.id);
 });
 strip.scrollLeft=left;layoutRecipeTabNames(view,true);
 if(wasHidden!==strip.hidden&&!view.restoreTabScroll&&panes.length===2){view.linkLayoutTransition=true;restoreRecipeLinkViewport(view,panes[0],panes[1],scroll,paneScroll)}
 if(focusKey){if(strip.hidden)view.close.focus({preventScroll:true});else [...strip.querySelectorAll('[role="tab"]')].find(b=>b.dataset.recipeTab===view.activeTab.key)?.focus({preventScroll:true})}
 view.cover.style.setProperty('--recipe-toolbar-height',view.close.parentElement.offsetHeight+'px');
}

function currentRecipeContext(day,category,meal){
 if(!day)return null;
 const entries=getDisplayedWeekdayMeals().filter(e=>e.day===day&&e.cat===category&&String(e.meal.id)===String(meal.id)),entry=entries.length===1?entries[0]:null;
 return entry?cookingContext(activePlanId,day,category,meal,entry.linkedTo):null;
}
function recipeOriginalUrl(meal){
 const value=String(meal.originalRecipeUrl||meal.sourceUrl||meal.url||meal.ingredientImportUrl||'').trim();
 try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)?u.href:''}catch(e){return ''}
}
// A display-only clear keeps source/import provenance available to matching and refresh.
function recipeDisplaySourceUrl(meal){return meal.recipeSourceHidden===true?'':recipeOriginalUrl(meal)}
function setRecipeToolbarIcon(button,kind,label){
 const paths={current:'<path d="M12 3v18M7 8l5-5 5 5M5 21h14"/>',recipes:'<rect x="3" y="5" width="13" height="16" rx="2"/><path d="M8 2h11a2 2 0 0 1 2 2v12M7 10h5M7 14h5"/>',heart:'<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z"/>',prep:'<path d="M4 5h16v16H4zM8 3v4M16 3v4M4 10h16M8 14h3M8 17h6"/>',delete:appIconSvg.delete,sound:'<path d="M11 5 6 9H3v6h3l5 4zM15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14"/>',stop:'<rect x="6" y="6" width="12" height="12" rx="1"/>',expand:'<path d="M6 9l6 6 6-6"/>',collapse:'<path d="M6 15l6-6 6 6"/>',timer:'<circle cx="12" cy="14" r="8"/><path d="M12 10v4l3 2M9 2h6M12 2v4M18 6l2-2"/>',pause:'<path d="M9 5v14M15 5v14"/>',play:'<path d="M8 4l12 8-12 8z"/>',bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',save:appIconSvg.save,edit:appIconSvg.rename,scale:'<rect x="3" y="13" width="8" height="8" rx="1"/><path d="M3 9V3h18v18h-6M13 11l7-7M14 4h6v6"/>',settings:appIconSvg.settings,close:appIconSvg.cancel,reset:'<path d="M3 12a9 9 0 1 0 9-9c-2.5 0-4.8 1-6.4 2.6L3 8"/><path d="M3 3v5h5"/>',split:'<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 12h16"/>',full:'<rect x="4" y="3" width="16" height="18" rx="2"/>'};
 button.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+paths[kind]+'</svg>';
 button.setAttribute('aria-label',label);button.title=label;
}
function buildRecipeViewerSettings(bar,inner){
 const settings=document.createElement('button');settings.type='button';settings.className='recipe-toolbar-icon recipe-settings-toggle';setRecipeToolbarIcon(settings,'settings','Recipe settings');settings.setAttribute('aria-expanded','false');settings.setAttribute('aria-controls','recipeViewerSettings');bar.append(settings);
 const cookingSettings=document.createElement('section');cookingSettings.id='recipeViewerSettings';cookingSettings.className='recipe-cooking-settings';cookingSettings.hidden=true;cookingSettings.setAttribute('role','region');cookingSettings.setAttribute('aria-label','Recipe settings');cookingSettings.addEventListener('wheel',()=>cancelRecipeAdvance(),{passive:true});
 const option=(text)=>{const label=document.createElement('label');label.className='recipe-auto-complete';const input=document.createElement('input');input.type='checkbox';label.append(input,document.createTextNode(text));cookingSettings.append(label);return input};
 const sync=option('Sync Ingredients'),autoComplete=option('Auto-complete Ingredients'),keepScreenAwake=option('Keep Screen Awake');
 const support=document.createElement('p');support.className='muted';support.textContent='Keeping the screen awake is unavailable in this browser.';support.hidden=typeof navigator.wakeLock?.request==='function';cookingSettings.append(support);

 buildCookingTimerVolumeControl(cookingSettings);
 const closeSettings=document.createElement('button');closeSettings.type='button';closeSettings.className='recipe-settings-close recipe-toolbar-icon';setRecipeToolbarIcon(closeSettings,'close','Close settings');cookingSettings.append(closeSettings);const dismiss=document.createElement('div');dismiss.className='recipe-settings-dismiss';dismiss.setAttribute('aria-hidden','true');inner.append(cookingSettings,dismiss);
 const display=open=>{cancelRecipeAdvance();cookingSettings.hidden=!open;settings.setAttribute('aria-expanded',String(open));if(!open){stopCookingTimerSound('test');settings.focus({preventScroll:true})}};settings.onclick=()=>display(cookingSettings.hidden);closeSettings.onclick=()=>display(false);
 // The backdrop catches content taps/drags; the toolbar remains accessible,
 // but its other actions consume the first tap to dismiss settings as well.
 inner.closest('#recipeViewer').addEventListener('click',e=>{
  if(!cookingSettings.hidden&&!cookingSettings.contains(e.target)&&!settings.contains(e.target)){
   e.preventDefault();e.stopImmediatePropagation();display(false);
  }
 },true);
 sync.onchange=()=>{recipeViewPrefs.syncIngredients=sync.checked;saveRecipeViewPrefs();if(recipeViewer)recipeViewer.syncRequested=true;renderRecipeViewer()};
 autoComplete.onchange=()=>{recipeViewPrefs.autoCompleteIngredients=autoComplete.checked;saveRecipeViewPrefs();cancelRecipeAdvance()};
 keepScreenAwake.onchange=()=>{recipeViewPrefs.keepScreenAwake=keepScreenAwake.checked;saveRecipeViewPrefs();const view=recipeViewer;if(!view)return;if(keepScreenAwake.checked){view.wakeRetries=0;acquireRecipeWakeLock()}else releaseRecipeWakeLock(view)};
 return {settings,cookingSettings,sync,autoComplete,keepScreenAwake};
}
function mealEditorSubsection(key,title,id,meal){
 const group=makeSettingsGroup(key,title);delete group.details.dataset.settingsGroup;group.details.classList.add('meal-editor-subsection');group.details.dataset.editorSubsection=key;group.details.id=id;
 group.details.open=false;return group;
}
function buildRecipeNotesSection(meal){
 const links=$('recipeIngredientLinks');links.open=false;
 const notes=$('recipeNotes'),label=notes.previousElementSibling,group=mealEditorSubsection('notes','Notes','editorNotesSection',meal);notes.value=String(meal.notes||'');links.after(group.details);group.content.id='recipeNotesPanel';label.htmlFor='recipeNotes';label.remove();notes.setAttribute('aria-label','Notes');group.content.append(notes);
}

// One deadline-based timer, independent of cooking progress and scheduled occurrences.
const COOKING_TIMER_KEY='mealRotationCookingTimerV1',COOKING_TIMER_MAX=30*24*60*60*1000,COOKING_TIMER_ALARM_MS=6000;
let cookingTimer=null,cookingTimerInterval=null,cookingTimerAudio=null,cookingTimerStarting=false,cookingTimerDismissDialog=null,cookingTimerSound=null;
function recipeCookingDurations(text){
 const source=String(text||'').replace(/\u00a0/g,' '),found=[];
 const numbers='(?:\\d+(?:\\s+\\d+\\/\\d+|[.,]\\d+|[½¼¾])?|\\d+\\/\\d+|[½¼¾]|one and a half|(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:[ -](?:one|two|three|four|five|six|seven|eight|nine))?|half(?: an?)?|quarter(?: of an?)?|an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)';
 // Written numbers need a boundary before the unit: 'as' is not 'a' + 's'.
 const pattern=new RegExp('(?:(?<![\\w./:])|(?<=[hms])(?=\\d))('+numbers+')(?:\\s*(?:–|—|-|to)\\s*('+numbers+'))?\\s*-?\\s*(?<![a-z])(hours?|hrs?|h|minutes?|mins?|min|m|seconds?|secs?|sec|s)(?![a-z])','gi');
 const words={a:1,an:1,one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10,eleven:11,twelve:12,thirteen:13,fourteen:14,fifteen:15,sixteen:16,seventeen:17,eighteen:18,nineteen:19,twenty:20,thirty:30,forty:40,fifty:50,sixty:60,seventy:70,eighty:80,ninety:90,'one and a half':1.5};
 const value=raw=>{let s=raw.toLowerCase().trim();if(s.startsWith('half'))return .5;if(s.startsWith('quarter'))return .25;if(s in words)return words[s];const compound=s.split(/[ -]/);if(compound.length===2&&compound.every(w=>w in words))return words[compound[0]]+words[compound[1]];let extra=0;s=s.replace(/[½¼¾]/,c=>{extra={'½':.5,'¼':.25,'¾':.75}[c];return ''});const f=s.match(/^(?:(\d+)\s+)?(\d+)\/(\d+)$/);return (f?Number(f[1]||0)+Number(f[2])/Number(f[3]):Number(s.replace(',','.')))+extra};
 for(const match of source.matchAll(pattern)){
  if(source[match.index-1]==='-')continue;
  // A spaced 'm' can mean metres. Accept it only with a clear timing/cooking cue.
  if(match[3].toLowerCase()==='m'&&/\s+m$/i.test(match[0])&&!/\b(cook|bake|simmer|rest|wait|roast|boil|steam|fry|chill|marinat\w*|for|every)\b/i.test(source.slice(Math.max(0,match.index-35),match.index)))continue;
  const factor=/^h/i.test(match[3])?3600000:/^m/i.test(match[3])?60000:1000;
  const ms=Math.round(Math.min(value(match[1]),match[2]?value(match[2]):Infinity)*factor);
  if(!Number.isFinite(ms)||ms<1000||ms>COOKING_TIMER_MAX)continue;
  const part={ms,factor,label:match[0],start:match.index,end:match.index+match[0].length};
  const previous=found[found.length-1],between=previous?source.slice(previous.end,part.start):'';
  if(previous&&/^\s*(?:–|—|-|to)\s*$/i.test(between)){previous.ms=Math.min(previous.ms,part.ms);previous.end=part.end;previous.label=source.slice(previous.start,part.end)}
  else if(previous&&part.factor<previous.factor&&(/^[\s,]*(?:and\s*)?$/i.test(between)||(/^\.\s*$/.test(between)&&/\b(?:hrs?|h|mins?|m|secs?|s)$/i.test(previous.label)))&&previous.ms+part.ms<=COOKING_TIMER_MAX){previous.ms+=part.ms;previous.factor=part.factor;previous.end=part.end;previous.label=source.slice(previous.start,part.end)}
  else found.push(part);
 }
 return found;
}
function readCookingTimer(){
 try{const t=JSON.parse(localStorage.getItem(COOKING_TIMER_KEY)||'null');if(!t||t.version!==1||typeof t.id!=='string'||!['running','paused','complete'].includes(t.status)||typeof t.recipeId!=='string'||typeof t.recipeName!=='string'||typeof t.stepToken!=='string'||typeof t.stepText!=='string')return null;if(t.status==='running'&&(!Number.isFinite(t.deadline)||t.deadline>Date.now()+COOKING_TIMER_MAX))return null;if(t.status==='paused'&&(!Number.isFinite(t.remaining)||t.remaining<=0||t.remaining>COOKING_TIMER_MAX))return null;return t}catch(e){return null}
}
function saveCookingTimer(){try{if(cookingTimer)localStorage.setItem(COOKING_TIMER_KEY,JSON.stringify(cookingTimer));else localStorage.removeItem(COOKING_TIMER_KEY)}catch(e){/* In-memory timer still works when storage is unavailable. */}}
function cookingTimerRemaining(){return !cookingTimer||cookingTimer.status==='complete'?0:cookingTimer.status==='paused'?cookingTimer.remaining:Math.max(0,cookingTimer.deadline-Date.now())}
function cookingTimerClock(ms){const s=Math.ceil(ms/1000),h=Math.floor(s/3600),m=Math.floor(s/60)%60;return h?h+':'+String(m).padStart(2,'0')+':'+String(s%60).padStart(2,'0'):m+':'+String(s%60).padStart(2,'0')}
function prepareCookingTimerAudio(){try{const Audio=window.AudioContext||window.webkitAudioContext;if(Audio){cookingTimerAudio||=new Audio();cookingTimerAudio.resume()?.catch(()=>{})}}catch(e){}}
function stopCookingTimerSound(kind=null){
 const sound=cookingTimerSound;if(!sound||kind&&sound.kind!==kind)return;
 cookingTimerSound=null;clearTimeout(sound.timeout);cookingTimerAudio?.removeEventListener?.('statechange',sound.stateChange);
 try{sound.gain.gain.setValueAtTime(0,cookingTimerAudio.currentTime)}catch(e){}
 try{sound.source.stop()}catch(e){}
 try{sound.source.disconnect();sound.gain.disconnect()}catch(e){}
 updateCookingTimerSoundControls();
}
function cookingTimerAlarmBuffer(ctx){
 // A bounded, alternating three-pulse tone is more noticeable than the old chime.
 const rate=ctx.sampleRate,buffer=ctx.createBuffer(1,Math.ceil(rate*2),rate),data=buffer.getChannelData(0);
 for(let i=0;i<data.length;i++){const time=i/rate,pulse=Math.floor(time/.32),within=time-pulse*.32;if(pulse>2||within>=.22)continue;const envelope=Math.min(1,within/.012,(.22-within)/.025),phase=2*Math.PI*(pulse===1?1100:880)*within;data[i]=.4*envelope*(.8*Math.sin(phase)+.2*Math.sin(phase*3))}
 return buffer;
}
function startCookingTimerSound(kind,timerId=null,endsAt=null){
 if(cookingTimerSound?.kind===kind&&cookingTimerSound.timerId===timerId)return;
 stopCookingTimerSound();if(kind==='test')prepareCookingTimerAudio();
 try{const ctx=cookingTimerAudio,stopAt=Math.min(endsAt||Infinity,Date.now()+(kind==='test'?3000:COOKING_TIMER_ALARM_MS)),duration=(stopAt-Date.now())/1000;
  if(!ctx||document.hidden||duration<=0||kind==='alarm'&&ctx.state!=='running')return;
  const source=ctx.createBufferSource(),gain=ctx.createGain();source.buffer=cookingTimerAlarmBuffer(ctx);source.loop=true;gain.gain.setValueAtTime(recipeViewPrefs.timerAlarmVolume,ctx.currentTime);source.connect(gain);gain.connect(ctx.destination);
  const sound={kind,timerId,source,gain,stopAt,timeout:null};cookingTimerSound=sound;
  sound.stateChange=()=>{if(cookingTimerSound===sound&&(Date.now()>=stopAt||kind==='alarm'&&ctx.state!=='running'))stopCookingTimerSound(kind)};ctx.addEventListener?.('statechange',sound.stateChange);
  source.onended=()=>{if(cookingTimerSound===sound){cookingTimerSound=null;clearTimeout(sound.timeout);ctx.removeEventListener?.('statechange',sound.stateChange);try{source.disconnect();gain.disconnect()}catch(e){}updateCookingTimerSoundControls()}};
  // Audio-renderer duration bounds playback even if JavaScript timers are delayed.
  source.start(0,0,duration);sound.timeout=setTimeout(()=>{if(cookingTimerSound===sound)stopCookingTimerSound(kind)},Math.max(0,stopAt-Date.now()));
 }catch(e){stopCookingTimerSound()}
 updateCookingTimerSoundControls();
}
function syncCookingTimerAlarm(){
 const sound=cookingTimerSound;
 if(sound?.kind==='alarm'&&(!cookingTimer||cookingTimer.status!=='complete'||sound.timerId!==cookingTimer.id||document.hidden||Date.now()>=sound.stopAt||cookingTimerAudio?.state!=='running'))stopCookingTimerSound('alarm');
 updateCookingTimerSoundControls();
}
function updateCookingTimerSoundControls(){
 const settings=recipeViewer?.cookingSettings;if(!settings)return;
 const notify=settings.querySelector('.recipe-timer-notifications');if(notify)notify.hidden=!(cookingTimer&&cookingTimer.status!=='complete'&&typeof window.Notification==='function'&&Notification.permission==='default'&&typeof Notification.requestPermission==='function');
 const preview=settings.querySelector('.recipe-timer-test-sound');if(preview){const testing=cookingTimerSound?.kind==='test';setRecipeToolbarIcon(preview,testing?'stop':'sound',testing?'Stop test sound':'Test alarm sound');preview.disabled=cookingTimer?.status==='complete';if(preview.disabled)preview.title='Dismiss the finished timer before testing the sound'}
 const slider=settings.querySelector('[data-timer-alarm-volume]'),output=settings.querySelector('.recipe-timer-volume-output');if(slider){slider.value=String(Math.round(recipeViewPrefs.timerAlarmVolume*100));slider.setAttribute('aria-valuetext',slider.value+'%');output.textContent=slider.value+'%'}
}
function setCookingTimerAlarmVolume(value){
 const percent=Math.max(0,Math.min(100,Number(value)));if(!Number.isFinite(percent))return;
 recipeViewPrefs.timerAlarmVolume=percent/100;saveRecipeViewPrefs();
 try{cookingTimerSound?.gain.gain.setValueAtTime(recipeViewPrefs.timerAlarmVolume,cookingTimerAudio.currentTime)}catch(e){}
 updateCookingTimerSoundControls();
}
function buildCookingTimerVolumeControl(settings){
 const row=document.createElement('div');row.className='recipe-timer-volume';
 const label=document.createElement('label');label.htmlFor='recipeTimerAlarmVolume';label.textContent='Timer alarm volume';
 const output=document.createElement('output');output.className='recipe-timer-volume-output';output.htmlFor='recipeTimerAlarmVolume';output.textContent=Math.round(recipeViewPrefs.timerAlarmVolume*100)+'%';
 const slider=document.createElement('input');slider.type='range';slider.id='recipeTimerAlarmVolume';slider.min='0';slider.max='100';slider.step='1';slider.dataset.timerAlarmVolume='';slider.value=String(Math.round(recipeViewPrefs.timerAlarmVolume*100));slider.setAttribute('aria-valuetext',slider.value+'%');slider.oninput=()=>setCookingTimerAlarmVolume(slider.value);
 const preview=document.createElement('button');preview.type='button';preview.className='recipe-timer-icon recipe-timer-test-sound';setRecipeToolbarIcon(preview,'sound','Test alarm sound');preview.onclick=()=>{if(cookingTimer?.status==='complete')return;if(cookingTimerSound?.kind==='test')stopCookingTimerSound('test');else startCookingTimerSound('test')};
 row.append(label,output,slider,preview);settings.append(row);
 const notify=document.createElement('button');notify.type='button';notify.className='recipe-timer-icon recipe-timer-notifications';setRecipeToolbarIcon(notify,'bell','Enable timer notifications');notify.hidden=true;notify.onclick=async()=>{try{await Notification.requestPermission()}catch(e){}syncCookingTimer()};settings.append(notify);
}

async function alertCookingTimer(timer){
 try{if(typeof window.Notification!=='function'||Notification.permission!=='granted')return;const options={body:timer.recipeName+' — '+timer.stepText,tag:'meal-rotation-cooking-timer-'+timer.id};const registration=await navigator.serviceWorker?.getRegistration?.();if(registration?.showNotification)await registration.showNotification('Cooking timer finished',options);else new Notification('Cooking timer finished',options)}catch(e){/* Mobile browsers may refuse notifications or audio. The finished state remains visible. */}
}
// A completion is handled once. Audio is only attempted while visible and within
// the original five-second deadline window; returning to the app never replays it.
let cookingTimerObservedId=null,cookingTimerAudibleId=null,cookingTimerCompletionDialog=null,cookingTimerCompletionFrame=null;
function suspendCookingTimerAlert(){cookingTimerAudibleId=null;stopCookingTimerSound()}
function closeCookingTimerCompletion(){
 const dialog=cookingTimerCompletionDialog;if(!dialog)return;cookingTimerCompletionDialog=null;dialog.cover.remove();
 for(const [el,was]of dialog.inert)if(el.isConnected)el.inert=was;
 if(dialog.focus?.isConnected)dialog.focus.focus({preventScroll:true});
}
function requestCookingTimerCompletion(){
 if(cookingTimerCompletionDialog&&(!cookingTimer||cookingTimer.status!=='complete'||cookingTimerCompletionDialog.id!==cookingTimer.id))closeCookingTimerCompletion();
 if(document.hidden||cookingTimer?.status!=='complete'||cookingTimerCompletionFrame!==null)return;
 cookingTimerCompletionFrame=requestAnimationFrame(()=>{cookingTimerCompletionFrame=null;if(document.hidden||cookingTimer?.status!=='complete')return;
  if(cookingTimerCompletionDialog){const dialog=cookingTimerCompletionDialog;for(const el of document.body.children)if(el!==dialog.cover){if(!dialog.inert.some(([prior])=>prior===el))dialog.inert.push([el,el.inert]);el.inert=true}dialog.cover.inert=false;dialog.cover.querySelector('button')?.focus({preventScroll:true});return}
  cookingTimerDismissDialog?.();recipeViewer?.openRecipesDialog?.();closeCookingTimerControls();
  const cover=document.createElement('div');cover.id='cookingTimerCompletion';cover.className='recipe-timer-dialog';cover.setAttribute('role','alertdialog');cover.setAttribute('aria-modal','true');cover.setAttribute('aria-labelledby','cookingTimerCompletionTitle');cover.setAttribute('aria-describedby','cookingTimerCompletionRecipe');
  const panel=document.createElement('div'),title=document.createElement('strong');title.id='cookingTimerCompletionTitle';title.textContent="Time's Up!";
  const name=document.createElement('p');name.id='cookingTimerCompletionRecipe';name.textContent=meals.find(m=>String(m.id)===String(cookingTimer.recipeId))?.name||cookingTimer.recipeName;
  const acknowledge=document.createElement('button');acknowledge.type='button';acknowledge.className='recipe-timer-icon';setRecipeToolbarIcon(acknowledge,'save','Acknowledge completed timer');acknowledge.onclick=cancelCookingTimer;panel.append(title,name,acknowledge);cover.append(panel);
  const focus=document.activeElement,inert=[...document.body.children].map(el=>[el,el.inert]);for(const [el]of inert)el.inert=true;
  cookingTimerCompletionDialog={cover,inert,focus,id:cookingTimer.id};document.body.append(cover);acknowledge.focus({preventScroll:true});
  cover.onkeydown=e=>{if(e.key==='Escape'||e.key==='Tab'){e.preventDefault();e.stopPropagation();acknowledge.focus({preventScroll:true})}};
  cover.addEventListener('wheel',e=>e.preventDefault(),{passive:false});cover.addEventListener('touchmove',e=>e.preventDefault(),{passive:false});
 });
}
function syncCookingTimer(){
 const now=Date.now();
 if(cookingTimer?.status==='running'&&cookingTimerRemaining()>0){cookingTimerObservedId=cookingTimer.id;if(!document.hidden)cookingTimerAudibleId=cookingTimer.id}
 if(cookingTimer?.status==='running'&&cookingTimerRemaining()===0){
  const prior=cookingTimer,endsAt=prior.deadline+COOKING_TIMER_ALARM_MS,audible=cookingTimerAudibleId===prior.id&&!document.hidden&&now<endsAt;
  cookingTimer={...prior,status:'complete',remaining:0,completedAt:prior.deadline,alertHandled:true};saveCookingTimer();
  if(!prior.alertHandled&&cookingTimerObservedId===prior.id)alertCookingTimer(cookingTimer);
  if(!prior.alertHandled&&audible)startCookingTimerSound('alarm',prior.id,endsAt);
 }else if(cookingTimer?.status==='complete'&&!cookingTimer.alertHandled){cookingTimer={...cookingTimer,alertHandled:true};saveCookingTimer()}
 if(cookingTimer?.status==='running'){if(!cookingTimerInterval)cookingTimerInterval=setInterval(syncCookingTimer,500)}else{clearInterval(cookingTimerInterval);cookingTimerInterval=null}
 syncCookingTimerAlarm();renderCookingTimer();requestCookingTimerCompletion();
}
function cancelCookingTimer(){stopCookingTimerSound();cookingTimer=null;saveCookingTimer();syncCookingTimer()}
function pauseCookingTimer(){syncCookingTimer();if(cookingTimer?.status!=='running')return;cookingTimer={...cookingTimer,status:'paused',remaining:cookingTimerRemaining()};saveCookingTimer();syncCookingTimer()}
function resumeCookingTimer(){if(cookingTimer?.status!=='paused')return;prepareCookingTimerAudio();cookingTimer={...cookingTimer,status:'running',deadline:Date.now()+cookingTimer.remaining};saveCookingTimer();syncCookingTimer()}
function cookingTimerDialog(title,choices,compact=false){return new Promise(resolve=>{
 const view=recipeViewer,shade=document.createElement('div');shade.className='recipe-timer-dialog'+(compact?' recipe-timer-confirm':'');shade.setAttribute('role','dialog');shade.setAttribute('aria-modal','true');shade.setAttribute('aria-label',title);
 const panel=document.createElement('div'),heading=document.createElement('strong');heading.textContent=title;panel.append(heading);const focused=document.activeElement,inert=[...document.body.children].map(el=>[el,el.inert]);inert.forEach(([el])=>el.inert=true);
 let settled=false;cookingTimerDismissDialog=()=>done(null);
 function done(value){if(settled)return;settled=true;cookingTimerDismissDialog=null;shade.remove();for(const [el,was]of inert)if(el.isConnected)el.inert=was;if(focused?.isConnected)focused.focus({preventScroll:true});resolve(recipeViewer===view?value:null)}
 const actions=document.createElement('div');if(compact){actions.className='recipe-timer-confirm-actions';panel.append(actions)}
 for(const choice of choices){const b=document.createElement('button');b.type='button';if(compact){b.className='recipe-timer-icon';setRecipeToolbarIcon(b,choice.value===true?'save':'close',choice.label)}else{b.className='smallbtn';b.textContent=choice.label}b.onclick=()=>done(choice.value);(compact?actions:panel).append(b)}
 const close=document.createElement('button');close.type='button';setRecipeToolbarIcon(close,'close','Cancel timer selection');close.className='recipe-timer-icon';close.onclick=()=>done(null);if(!compact)panel.append(close);shade.append(panel);document.body.append(shade);(compact?actions.lastElementChild:close).focus({preventScroll:true});shade.onclick=e=>{if(e.target===shade)done(null)};shade.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();done(null)}if(e.key==='Tab'){const buttons=[...panel.querySelectorAll('button')],first=buttons[0],last=buttons[buttons.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}};
 })}
async function startRecipeCookingTimer(meal,item,durations,stepNumber){
 if(cookingTimerStarting||!recipeViewer||recipeViewer.mealId!==String(meal.id))return;
 if(cookingTimer&&recipeViewer.hiddenTimerId===cookingTimer.id&&String(cookingTimer.recipeId)===String(meal.id)&&cookingTimer.stepToken===item.token){showRecipeCookingTimer();return}
 cookingTimerStarting=true;prepareCookingTimerAudio();const view=recipeViewer;
 try{
  let duration=durations[0];
  if(durations.length>1){const index=await cookingTimerDialog('Choose cooking duration',durations.map((d,i)=>({label:(i+1)+'. '+d.label+' · '+item.text.slice(Math.max(0,d.start-24),Math.min(item.text.length,d.end+24)),value:i})));if(index===null)return;duration=durations[index]}
  if(recipeViewer!==view)return;
  syncCookingTimer();if(cookingTimer){const replace=await cookingTimerDialog('Replace current timer?',[{label:'Replace timer',value:true},{label:'Keep current timer',value:false}],true);if(replace!==true||recipeViewer!==view)return}
  cookingTimer={version:1,id:Date.now().toString(36)+'-'+Math.random().toString(36).slice(2),recipeId:String(meal.id),recipeName:meal.name||'Recipe',stepToken:item.token,stepText:item.text,stepNumber,context:view.context?{...view.context}:null,status:'running',deadline:Date.now()+duration.ms,remaining:duration.ms};saveCookingTimer();syncCookingTimer();
 }finally{cookingTimerStarting=false}
}
function addRecipeCookingTimer(li,meal,item,stepNumber){
 const durations=recipeCookingDurations(item.text);if(!durations.length)return;
 li.classList.add('recipe-timed-step');const b=document.createElement('button');b.type='button';b.className='recipe-timer-icon recipe-step-timer';setRecipeToolbarIcon(b,'timer',durations.length===1?'Start timer: '+durations[0].label:'Choose timer duration');
 for(const event of ['pointerdown','pointerup','touchstart','touchend','dblclick'])b.addEventListener(event,e=>e.stopPropagation());
 b.onclick=e=>{e.preventDefault();e.stopPropagation();startRecipeCookingTimer(meal,item,durations,stepNumber)};li.append(b);
}
// List indicators consume the one existing timer record; names bind by stable recipe ID.
let cookingTimerControlsDialog=null;
function bindRecipeTimerName(name,meal,showFavorite=true){name.dataset.recipeTimerName=String(meal.id);updateRecipeTimerName(name);bindRecipePersonalName(name,meal,showFavorite)}
function updateRecipeTimerName(name){
 const active=!!cookingTimer&&name.dataset.recipeTimerName===String(cookingTimer.recipeId);
 let wrap=name.parentElement?.classList.contains('recipe-name-with-timer')?name.parentElement:null;
 if(!active){if(wrap){wrap.replaceWith(name)}return}
 if(!wrap){wrap=document.createElement('span');wrap.className='recipe-name-with-timer';name.replaceWith(wrap);wrap.append(name);const icon=document.createElement('button');icon.type='button';icon.className='recipe-list-timer';
  for(const event of ['pointerdown','pointerup','touchstart','touchend','dblclick'])icon.addEventListener(event,e=>e.stopPropagation());
  icon.onclick=e=>{e.preventDefault();e.stopPropagation();if(cookingTimer&&String(cookingTimer.recipeId)===name.dataset.recipeTimerName)openCookingTimerControls()};wrap.append(icon)}
 const icon=wrap.querySelector('.recipe-list-timer'),label=(cookingTimer.status==='complete'?'Finished':cookingTimer.status==='paused'?'Paused':'Running')+' timer: '+(meals.find(m=>String(m.id)===String(cookingTimer.recipeId))?.name||cookingTimer.recipeName);
 if(icon.getAttribute('aria-label')!==label)setRecipeToolbarIcon(icon,'timer',label);
 icon.dataset.timerStatus=cookingTimer.status;
}
function refreshRecipeTimerIndicators(){document.querySelectorAll('#list [data-recipe-timer-name]').forEach(updateRecipeTimerName)}
function closeCookingTimerControls(){
 const dialog=cookingTimerControlsDialog;if(!dialog)return;cookingTimerControlsDialog=null;window.removeEventListener('popstate',closeCookingTimerControls);dialog.cover.remove();
 for(const [el,was]of dialog.inert)if(el.isConnected)el.inert=was;
 if(dialog.focus?.isConnected)dialog.focus.focus({preventScroll:true});else [...document.querySelectorAll('#list [data-recipe-timer-name]')].find(el=>el.dataset.recipeTimerName===dialog.recipeId)?.focus({preventScroll:true});
}
function openCookingTimerControls(){
 if(!cookingTimer||cookingTimerControlsDialog)return;
 const cover=document.createElement('div');cover.id='cookingTimerControlsDialog';cover.className='recipe-timer-dialog';cover.setAttribute('role','dialog');cover.setAttribute('aria-modal','true');cover.setAttribute('aria-label','Cooking timer');
 const panel=document.createElement('div');
 const focus=document.activeElement,inert=[...document.body.children].map(el=>[el,el.inert]);inert.forEach(([el])=>el.inert=true);
 cookingTimerControlsDialog={cover,panel,focus,inert,recipeId:String(cookingTimer.recipeId)};cover.append(panel);document.body.append(cover);
 cover.onclick=e=>{if(e.target===cover)closeCookingTimerControls()};cover.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();closeCookingTimerControls()}if(e.key==='Tab'){const buttons=[...cover.querySelectorAll('button:not([disabled])')],first=buttons[0],last=buttons.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}};
 window.addEventListener('popstate',closeCookingTimerControls);syncCookingTimer();panel.querySelector('button:not([disabled])')?.focus({preventScroll:true});
}

function showRecipeCookingTimer(){if(!recipeViewer||!cookingTimer)return;recipeViewer.hiddenTimerId=null;renderCookingTimer()}
function hideRecipeCookingTimer(){if(!recipeViewer||!cookingTimer)return;recipeViewer.hiddenTimerId=cookingTimer.id;renderCookingTimer()}
function updateRecipeTimerReopenControl(){
 const view=recipeViewer,actions=view?.cover.querySelector('.recipe-title-actions');if(!actions)return;
 let button=actions.querySelector('.recipe-timer-reopen');
 if(!cookingTimer||view.hiddenTimerId!==cookingTimer.id){button?.remove();return}
 if(!button){button=document.createElement('button');button.type='button';button.className='recipe-header-icon recipe-timer-reopen';setRecipeToolbarIcon(button,'timer','Show timer');button.onclick=showRecipeCookingTimer;actions.append(button)}
}
function renderCookingTimerSurface(bar,hide){
 let strip=bar.querySelector('.recipe-timer-strip');
 if(!cookingTimer){strip?.remove();return}
 const key=cookingTimer.id+':'+cookingTimer.status;
 if(!strip||strip.dataset.timerState!==key){
  strip?.remove();strip=document.createElement('div');strip.className='recipe-timer-strip';strip.dataset.timerState=key;
  const readout=document.createElement('div');readout.className='recipe-timer-readout';readout.setAttribute('role','timer');readout.setAttribute('aria-live','off');strip.append(readout);
  const controls=document.createElement('div');controls.className='recipe-timer-controls';
  const control=(kind,label,action,disabled=false)=>{const b=document.createElement('button');b.type='button';b.className='recipe-timer-icon';setRecipeToolbarIcon(b,kind,label);b.disabled=disabled;b.onclick=action;controls.append(b)};
  const complete=cookingTimer.status==='complete',paused=cookingTimer.status==='paused';
  control(paused||complete?'play':'pause',complete?'Timer finished':paused?'Resume timer':'Pause timer',paused?resumeCookingTimer:pauseCookingTimer,complete);
  control('close','Hide timer controls',hide);
  control('delete','Delete timer',cancelCookingTimer);
  strip.append(controls);bar.append(strip);
  if(complete){strip.classList.add('recipe-timer-finished');const notice=document.createElement('span');notice.className='recipe-timer-announcement';notice.setAttribute('role','status');notice.textContent='Cooking timer finished';strip.append(notice)}
 }
 const clock=cookingTimerClock(cookingTimerRemaining()).padStart(5,'0'),readout=strip.querySelector('.recipe-timer-readout');readout.textContent=clock;readout.classList.toggle('recipe-timer-long',clock.length>5);readout.setAttribute('aria-label',(cookingTimer.status==='complete'?'Finished':cookingTimer.status==='paused'?'Paused':'Running')+' timer: '+clock);
}
function renderCookingTimer(){
 refreshRecipeTimerIndicators();updateRecipeTimerReopenControl();
 const view=recipeViewer,bar=view?.cover.querySelector('.recipe-viewer-bar');
 if(bar){if(cookingTimer&&view.hiddenTimerId===cookingTimer.id)bar.querySelector('.recipe-timer-strip')?.remove();else renderCookingTimerSurface(bar,hideRecipeCookingTimer)}
 if(cookingTimerControlsDialog){if(!cookingTimer)closeCookingTimerControls();else renderCookingTimerSurface(cookingTimerControlsDialog.panel,closeCookingTimerControls)}
}
cookingTimer=readCookingTimer();
window.addEventListener('focus',syncCookingTimer);window.addEventListener('pageshow',syncCookingTimer);document.addEventListener('visibilitychange',()=>{if(document.hidden)suspendCookingTimerAlert();else syncCookingTimer()});window.addEventListener('pagehide',suspendCookingTimerAlert);document.addEventListener('freeze',suspendCookingTimerAlert);
window.addEventListener('storage',e=>{if(e.key===null||e.key===COOKING_TIMER_KEY){cookingTimer=readCookingTimer();syncCookingTimer()}});

function revealRecipeAssociation(ingredientToken,stepToken){
 const view=recipeViewer;if(!view)return;cancelRecipeAdvance(view);view.cancelIngredientSync?.();
 if(stepToken){view.syncPinnedStep=stepToken;view.syncGeometryHold=true}
 requestAnimationFrame(()=>{if(recipeViewer!==view)return;
  for(const [pane,token]of [['.recipe-ingredients-pane',ingredientToken],['.recipe-instructions-pane',stepToken]]){
   const container=view.content.querySelector(pane),target=[...container.querySelectorAll('[data-cooking-token]')].find(el=>el.dataset.cookingToken===token);if(!target)continue;
   const scroller=recipeViewingMode()==='split'?container:view.cover;
   scroller.scrollTop+=target.getBoundingClientRect().top-scroller.getBoundingClientRect().top-(scroller===view.cover?view.close.parentElement.offsetHeight+12:12);
  }
 });
}
function revealGroceryRecipeIngredient(meal,line){
 if(recipeViewer?.mealId!==String(meal.id))return;
 const ingredient=cookingItemTokens(meal).ingredients.find(item=>item.text.trim()===String(line).trim());if(!ingredient)return;
 const step=[...recipeIngredientMatches(meal)].find(([,tokens])=>tokens.includes(ingredient.token))?.[0];
 if(step)revealRecipeAssociation(ingredient.token,step);
}
function configureCurrentRecipeStep(view,meal,session){
 view.currentStepCleanup?.();const button=view.cover.querySelector('.recipe-current-step'),pane=view.content.querySelector('.recipe-instructions-pane');
 let frame=0;
 const update=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
  if(recipeViewer!==view)return;
  const step=cookingItemTokens(meal).steps.find(item=>item.token&&cleanInstructionBlock(item).type!=='section'&&!session?.steps.includes(item.token));
  const target=step&&[...pane.querySelectorAll('[data-cooking-token]')].find(el=>el.dataset.cookingToken===step.token);
  button.hidden=true;if(!target||view.linkEdit)return;
  const split=recipeViewingMode()==='split',bounds=(split?pane:view.cover).getBoundingClientRect(),rect=target.getBoundingClientRect();
  const top=split?bounds.top:Math.max(bounds.top,view.close.parentElement.getBoundingClientRect().bottom),bottom=Math.min(bounds.bottom,window.visualViewport?window.visualViewport.offsetTop+window.visualViewport.height:innerHeight);
  if(rect.bottom>top&&rect.top<bottom)return;
  const direction=rect.bottom<=top?'up':'down';button.dataset.direction=direction;setRecipeToolbarIcon(button,direction==='up'?'collapse':'expand','Return to unfinished step');button.hidden=false;
 })};
 view.cover.addEventListener('scroll',update,{capture:true,passive:true});window.addEventListener('resize',update);window.visualViewport?.addEventListener('resize',update);
 const observer=new ResizeObserver(update);observer.observe(pane);observer.observe(view.content);
 view.currentStepCleanup=()=>{cancelAnimationFrame(frame);observer.disconnect();view.cover.removeEventListener('scroll',update,true);window.removeEventListener('resize',update);window.visualViewport?.removeEventListener('resize',update)};update();
}
function returnToCurrentRecipeStep(){
 const view=recipeViewer,meal=meals.find(m=>String(m.id)===view?.mealId);if(!meal||view.linkEdit)return;
 const session=view.context?cookingSession(view.context):view.previewProgress;
 const step=cookingItemTokens(meal).steps.find(item=>item.token&&cleanInstructionBlock(item).type!=='section'&&!session?.steps.includes(item.token));
 if(step)revealRecipeAssociation(null,step.token);
}
function openRecipeViewer(meal,context=null,pushHistory=true,savedTabs=null,navigationOrigin=null){
 const origin=navigationOrigin||recipeViewer?.navigationOrigin||captureMealEditorOrigin();
 if(recipeViewer?.linkEdit){recipeLinkMessage(recipeViewer,'Save or cancel the current ingredient links before opening another recipe.');return}
 if(recipeViewer){if(pushHistory&&window.history.state?.mealRotationRecipeViewer)window.history.replaceState({...window.history.state,mealRotationRecipeViewer:{...window.history.state.mealRotationRecipeViewer,scrollTop:recipeViewer.cover.scrollTop}},'');finishRecipeViewerClose(false)}
 const returnFocus=document.activeElement,scroll=window.scrollY,overflow=document.body.style.overflow;
 const cover=document.createElement('section');cover.id='recipeViewer';cover.setAttribute('role','dialog');cover.setAttribute('aria-modal','true');cover.setAttribute('aria-label','Recipe: '+(meal.name||'Untitled meal'));
 const inner=document.createElement('div');inner.className='recipe-viewer-content';cover.append(inner);
 const bar=document.createElement('header');bar.className='recipe-viewer-bar';const close=document.createElement('button');close.type='button';close.className='recipe-toolbar-icon';setRecipeToolbarIcon(close,'close','Close recipe');close.onclick=closeRecipeViewer;bar.append(close);
 const reset=document.createElement('button');reset.type='button';reset.className='recipe-toolbar-icon recipe-reset';setRecipeToolbarIcon(reset,'reset','Reset Progress');reset.onclick=()=>{const view=recipeViewer;if(!view)return;cancelRecipeAdvance();if(view.context){const key=cookingOccurrenceKey(view.context);resetCookingContexts(c=>cookingOccurrenceKey(c)===key)}else view.previewProgress={ingredients:[],steps:[]};renderRecipeViewer()};bar.append(reset);const mode=document.createElement('button');mode.type='button';mode.className='recipe-toolbar-icon recipe-view-mode';mode.onclick=()=>{const view=recipeViewer;if(!view)return;captureRecipeTab(view);view.activeTab.mode=recipeViewingMode()==='split'?'full':'split';recipeViewPrefs.mode=view.activeTab.mode;saveRecipeViewPrefs();view.restoreTabScroll=true;view.syncRequested=true;renderRecipeViewer()};bar.append(mode);const current=document.createElement('button');current.type='button';current.className='recipe-toolbar-icon recipe-current-step';setRecipeToolbarIcon(current,'current','Return to current step');current.onclick=returnToCurrentRecipeStep;cover.append(current);inner.append(bar);const {settings,cookingSettings,sync,autoComplete,keepScreenAwake}=buildRecipeViewerSettings(bar,inner);const openRecipes=document.createElement('button');openRecipes.type='button';openRecipes.className='recipe-toolbar-icon recipe-open-recipes';setRecipeToolbarIcon(openRecipes,'recipes','Open recipes');openRecipes.onclick=openViewerRecipes;bar.append(openRecipes);
 const content=document.createElement('article');inner.append(content);
 const inert=[...document.body.children].map(e=>[e,e.inert]);for(const [e] of inert)e.inert=true;
 recipeViewer={navigationOrigin:origin,scheduleOrigin:savedTabs?.scheduleOrigin||recipeScheduleOrigin(meal,context),mealId:String(meal.id),context,cover,content,close,reset,mode,settings,sync,cookingSettings,autoComplete,keepScreenAwake,inert,returnFocus,scroll,overflow,wake:null,wakeRequest:0,importController:null,previewProgress:{ingredients:[],steps:[]}};
 cover.dataset.recoveryDraft='recipe-viewer';cover.mealRecoveryDraft={ownerId:'viewer:'+meal.id,kind:'recipe-viewer',capture:()=>{const view=recipeViewer;if(!view||view.cover!==cover)return null;return {recipeId:view.mealId,context:view.context,previewProgress:view.previewProgress,previewScale:view.previewScale,ingredientLinkDraft:view.linkEdit?{...view.linkEdit,selected:[...view.linkEdit.selected]}:null}},dirty:()=>recipeViewer?.cover===cover&&!!recipeViewer.linkEdit,discard:()=>{if(recipeViewer?.cover===cover&&recipeViewer.linkEdit)finishRecipeLinkEdit(false)}};
 installRecipeViewerTabs(recipeViewer,meal,context,savedTabs);context=recipeViewer.anchorTab.context;
 document.body.append(cover);document.body.style.overflow='hidden';
 cover.addEventListener('pointerdown',()=>{recipeViewer&& (recipeViewer.suppressLinkGestureClick=false)},{capture:true});
 cover.addEventListener('click',e=>{if(recipeViewer?.suppressLinkGestureClick){recipeViewer.suppressLinkGestureClick=false;e.preventDefault();e.stopImmediatePropagation()}},{capture:true});
 cover.addEventListener('keydown',()=>{if(recipeViewer)recipeViewer.suppressLinkGestureClick=false},{capture:true});
 if(pushHistory)window.history.pushState({...window.history.state,mealRotationRecipeViewer:{mealId:String(meal.id),context}},'');
 renderRecipeViewer();syncCookingTimer();close.focus();cover.addEventListener('keydown',e=>{
  if(e.key==='Escape'){e.preventDefault();if(recipeViewer?.linkEdit&&cookingSettings.hidden){finishRecipeLinkEdit(false);return}if(!cookingSettings.hidden){cookingSettings.hidden=true;settings.setAttribute('aria-expanded','false');settings.focus({preventScroll:true})}else closeRecipeViewer()}
  if(e.key==='Tab'){const buttons=[...cover.querySelectorAll('button:not([disabled]):not([hidden]),a[href],input:not([disabled]),select:not([disabled]),summary')].filter(e=>e.getClientRects().length);const first=buttons[0],last=buttons[buttons.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}
 });
 if(typeof acquireRecipeWakeLock==='function')acquireRecipeWakeLock();
 if(typeof enrichViewedRecipe==='function')enrichViewedRecipe(meal);
}
function finishRecipeViewerClose(resumeOrigin=true){
 cookingTimerDismissDialog?.();recipeViewer?.openRecipesDialog?.();stopCookingTimerSound('test');
 const view=recipeViewer;if(!view)return;closeCookingTimerCompletion();recipeViewer=null;view.importController?.abort();view.resizeObserver?.disconnect();view.tabResizeObserver?.disconnect();view.tabDragCleanup?.();view.dividerGestureCleanup?.();view.syncCleanup?.();view.guidedCleanup?.();view.scaleCleanup?.();clearRecipeLinkGestures(view);cancelRecipeAdvance(view);

 if(typeof releaseRecipeWakeLock==='function')releaseRecipeWakeLock(view);
 view.currentStepCleanup?.();view.cover.remove();document.body.style.overflow=view.overflow;
 for(const [e,was] of view.inert)if(e.isConnected)e.inert=was;
 if(view.contentChanged)render();requestRecipeImportResume();
 view.returnFocus?.isConnected&&view.returnFocus.focus({preventScroll:true});window.scrollTo(0,view.scroll);
 if(resumeOrigin)view.navigationOrigin?.resumeDialog?.();requestCookingTimerCompletion();
}
function closeRecipeViewer(){
 if(recipeViewer?.contentEdit)return;
 if(recipeViewer?.linkEdit){recipeLinkMessage(recipeViewer,'Save or cancel the current ingredient links before closing the recipe.');return}
 const state=window.history.state?.mealRotationRecipeViewer;finishRecipeViewerClose();
 if(state){recipeViewerHistoryClosing=true;window.history.back()}
}
window.addEventListener('popstate',e=>{
 if(recipeViewer?.contentEdit){const view=recipeViewer;window.history.pushState({...e.state,mealRotationRecipeViewer:{mealId:view.mealId,context:view.context}},'');e.stopImmediatePropagation();return}
 if(recipeViewer?.linkEdit){const view=recipeViewer;window.history.pushState({...e.state,mealRotationRecipeViewer:{mealId:view.mealId,context:view.context}},'');recipeLinkMessage(view,'Save or cancel the current ingredient links before leaving the recipe.');e.stopImmediatePropagation();return}
 if(recipeEditorReturn&&!recipeViewer){
  // Back consumed the suspended viewer entry; restore it before returning to that dialog.
  window.history.pushState({...e.state,mealRotationRecipeViewer:{mealId:recipeEditorReturn.mealId,context:recipeEditorReturn.context}},'');
  rollbackEditorCategories();editId=null;restoreMealEditorScroll();e.stopImmediatePropagation();return;
 }
 if(recipeViewerHistoryClosing){recipeViewerHistoryClosing=false;restoreRecipeViewerHistory(e.state?.mealRotationRecipeViewer);e.stopImmediatePropagation();return}
 if(recipeViewer){finishRecipeViewerClose();restoreRecipeViewerHistory(e.state?.mealRotationRecipeViewer);e.stopImmediatePropagation();return}
 if(e.state?.mealRotationRecipeViewer){const m=meals.find(m=>String(m.id)===String(e.state.mealRotationRecipeViewer.mealId));if(m){openRecipeViewer(m,e.state.mealRotationRecipeViewer.context,false);e.stopImmediatePropagation()}}
},true);
function restoreRecipeViewerHistory(saved){
 if(!saved)return;const meal=meals.find(m=>String(m.id)===String(saved.mealId));if(meal){openRecipeViewer(meal,saved.context||null,false);recipeViewer.cover.scrollTop=saved.scrollTop||0}
}
function resumeRecipeViewer(){try{restoreRecipeViewerHistory(window.history.state?.mealRotationRecipeViewer);mealPersistence.finishStartup()}catch(error){mealPersistence.failStartup(error)}}
function recipeGuidanceEnabled(){return recipeViewingMode()==='split'&&recipeViewPrefs.syncIngredients===true}
function cancelRecipeAdvance(view=recipeViewer){if(!view)return;clearTimeout(view.advanceTimer);view.advanceTimer=null}
function configureGuidedCooking(view,ingredientsPane,instructionsPane){
 view.guidedCleanup?.();const events=new AbortController();
 const cancel=()=>cancelRecipeAdvance(view);
 const on=(el,event,fn,options={})=>el.addEventListener(event,fn,{...options,signal:events.signal});
 on(view.cover,'pointerdown',cancel,{capture:true});
 on(view.cover,'keydown',e=>{if(['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' ','Enter','Escape','Tab'].includes(e.key))cancel()},{capture:true});
 for(const pane of [ingredientsPane,instructionsPane])for(const event of ['wheel','touchmove'])on(pane,event,cancel,{passive:true});
 // Restoring a pane after a tap can emit a scroll event at the saved position; ignore that.
 on(instructionsPane,'scroll',()=>{if(view.advanceTimer!=null&&Math.abs(instructionsPane.scrollTop-view.advanceScrollTop)>.5)cancel()},{passive:true});
 on(window,'resize',cancel);on(document,'visibilitychange',()=>{if(document.visibilityState!=='visible')cancel()});
 view.guidedCleanup=()=>{cancel();events.abort()};
}
function recipeAdvanceSpacer(view,pane){
 let space=pane.querySelector('.recipe-advance-space');
 if(!space){space=document.createElement('div');space.className='recipe-advance-space';space.setAttribute('aria-hidden','true');pane.append(space)}
 space.style.height=(view.advanceSpace||0)+'px';return space;
}
function scheduleRecipeAdvance(view,token){
 if(view.linkEdit||!recipeGuidanceEnabled())return;
 const pane=view.content.querySelector('.recipe-instructions-pane'),buttons=[...pane.querySelectorAll('[data-cooking-token]')];
 const index=buttons.findIndex(b=>b.dataset.cookingToken===token);if(index<0)return;
 view.advanceScrollTop=pane.scrollTop;
 view.advanceTimer=setTimeout(()=>{
  view.advanceTimer=null;
  if(recipeViewer!==view||!recipeGuidanceEnabled()||!pane.isConnected||document.visibilityState!=='visible')return;
  const session=view.context?cookingSession(view.context):view.previewProgress;if(!session?.steps.includes(token))return;
  const completed=new Set(session.steps),incomplete=b=>!completed.has(b.dataset.cookingToken);
  const next=buttons.slice(index+1).find(incomplete)||buttons.slice(0,index).find(incomplete);
  if(!next?.isConnected)return;
  view.syncGeometryHold=false;view.syncToInstruction?.(next.dataset.cookingToken);
  const top=Math.max(0,pane.scrollTop+next.getBoundingClientRect().top-pane.getBoundingClientRect().top-12);
  if(top>pane.scrollHeight-pane.clientHeight){
   // Add only the trailing room needed to align a short final step. Retain it
   // across tap renders so undoing a step cannot clamp the reading position.
   const space=recipeAdvanceSpacer(view,pane),existing=view.advanceSpace||0,trial=Math.max(existing,pane.clientHeight);
   space.style.height=trial+'px';view.advanceSpace=Math.max(existing,Math.ceil(trial+top+pane.clientHeight-pane.scrollHeight));space.style.height=view.advanceSpace+'px';
  }
  pane.scrollTo({top,behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
 },350);
}
function toggleCookingItem(kind,token){
 const view=recipeViewer;if(!view||view.linkEdit)return;cancelRecipeAdvance(view);
 const meal=meals.find(m=>String(m.id)===view.mealId);if(!meal)return;
 let next,session;
 if(view.context){if(!cookingSession(view.context,true))return;next=JSON.parse(JSON.stringify(cookingSessions));session=next.occurrences[cookingOccurrenceKey(view.context)]}
 else session=JSON.parse(JSON.stringify(view.previewProgress));
 const completing=!session[kind].includes(token);
 if(kind==='ingredients'){prepareIngredientChoices(session);session.ingredientOverrides[token]=completing;materializeIngredientChoices(session)}
 else{
  let newlyCompleted=[token];
  if(completing){
   if(recipeGuidanceEnabled()){
    // Follow the displayed step order, excluding section headings, and retain
    // stable item tokens so each scheduled occurrence keeps its own progress.
    const steps=cookingItemTokens(meal).steps.filter(s=>s.type==='step'&&cleanInstructionBlock(s).type==='step');
    const index=steps.findIndex(s=>s.token===token);
    if(index>=0)newlyCompleted=steps.slice(0,index+1).map(s=>s.token).filter(t=>!session.steps.includes(t));
   }
   session.steps=[...new Set([...session.steps,...newlyCompleted])];
  }else session.steps=session.steps.filter(t=>t!==token);
  const automatic=completing&&recipeViewPrefs.autoCompleteIngredients;
  if(automatic||session.autoIngredients?.length)updateAutomaticCookingIngredients(session,meal,automatic?newlyCompleted:null);
 }
 if(view.context){if(!writeCookingSessions(next))return}else view.previewProgress=session;
 renderRecipeViewer();
 if(kind==='steps'&&completing)scheduleRecipeAdvance(view,token);
}
function buildRecipeTitleHeader(view,meal,multiplier){
 const header=document.createElement('div');header.className='recipe-header';
 const title=document.createElement('h1');title.textContent=meal.name||'Untitled meal';
 const actions=document.createElement('div');actions.className='recipe-title-actions';
 const edit=document.createElement('button');edit.type='button';edit.className='recipe-header-icon';setRecipeToolbarIcon(edit,'edit','Edit Recipe');edit.onclick=openViewedRecipeEditor;
 const wrap=document.createElement('div');wrap.className='recipe-scale-wrap';
 const scale=document.createElement('button');scale.type='button';scale.className='recipe-header-icon';setRecipeToolbarIcon(scale,'scale','Scale Recipe');scale.setAttribute('aria-haspopup','menu');scale.setAttribute('aria-expanded','false');scale.setAttribute('aria-controls','recipeScaleMenu');
 const menu=document.createElement('div');menu.id='recipeScaleMenu';menu.className='recipe-scale-menu';menu.hidden=true;menu.setAttribute('role','menu');menu.setAttribute('aria-label','Recipe scale');
 const dismiss=document.createElement('div');dismiss.className='recipe-scale-dismiss';dismiss.hidden=true;dismiss.setAttribute('aria-hidden','true');
 const events=new AbortController();
 const display=open=>{
  cancelRecipeAdvance(view);menu.hidden=!open;dismiss.hidden=!open;scale.setAttribute('aria-expanded',String(open));
  if(open){
   const anchor=scale.getBoundingClientRect(),box=menu.getBoundingClientRect(),vv=window.visualViewport,top=vv?.offsetTop||0,left=vv?.offsetLeft||0,width=vv?.width||window.innerWidth,height=vv?.height||window.innerHeight;
   const toolbarBottom=view.close.parentElement.getBoundingClientRect().bottom;
   menu.style.left=Math.max(left+8,Math.min(anchor.right-box.width,left+width-box.width-8))+'px';
   menu.style.top=Math.max(toolbarBottom+8,Math.min(anchor.bottom+6,top+height-box.height-8))+'px';
   const selected=menu.querySelector('[aria-checked="true"]');selected?.focus({preventScroll:true});
   if(selected)menu.scrollTop=Math.max(0,selected.offsetTop-menu.clientHeight/2);
  }else scale.focus({preventScroll:true});
 };
 for(const [value,text] of [[.5,'½×'],[1,'1×'],[1.5,'1½×'],[2,'2×'],[3,'3×']]){
  const option=document.createElement('button');option.type='button';option.className='recipe-scale-option';option.textContent=text;option.setAttribute('role','menuitemradio');option.setAttribute('aria-checked',String(value===multiplier));
  option.onclick=()=>{display(false);setViewedRecipeScale(value)};menu.append(option);
 }
 const custom=document.createElement('label');custom.className='recipe-scale-custom';custom.textContent='Custom multiplier';
 const input=document.createElement('input');input.type='number';input.inputMode='decimal';input.min='0';input.step='any';input.value=String(multiplier);input.setAttribute('aria-label','Custom multiplier');
 const apply=document.createElement('button');apply.type='button';apply.className='recipe-scale-option';apply.textContent='Apply multiplier';
 const commit=()=>{const value=input.value.trim()?Number(input.value):NaN;if(!validRecipeMultiplier(value)){input.setCustomValidity('Enter a number greater than zero.');input.reportValidity();return}input.setCustomValidity('');display(false);setViewedRecipeScale(value)};
 input.oninput=()=>input.setCustomValidity('');input.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();commit()}};apply.onclick=commit;custom.append(input);menu.append(custom,apply);
 scale.title='Scale Recipe · '+multiplier+'×';
 scale.onclick=()=>display(menu.hidden);
 view.cover.addEventListener('click',e=>{
  if(!menu.hidden&&!wrap.contains(e.target)){e.preventDefault();e.stopImmediatePropagation();display(false)}
 },{capture:true,signal:events.signal});
 view.cover.addEventListener('keydown',e=>{
  if(menu.hidden)return;
  if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();display(false)}
  else if(!e.target.matches('input')&&['ArrowDown','ArrowUp','Home','End'].includes(e.key)){
   e.preventDefault();e.stopImmediatePropagation();const options=[...menu.querySelectorAll('button,input')],index=options.indexOf(document.activeElement);
   const target=e.key==='Home'?0:e.key==='End'?options.length-1:(index+(e.key==='ArrowDown'?1:-1)+options.length)%options.length;options[target].focus({preventScroll:true});
  }
 },{capture:true,signal:events.signal});
 view.cover.addEventListener('scroll',()=>{if(!menu.hidden)display(false)},{signal:events.signal});
 const resizeScaleMenu=()=>{if(menu.hidden)return;if(document.activeElement!==input){display(false);return}const vv=window.visualViewport,top=(vv?.offsetTop||0)+view.close.parentElement.getBoundingClientRect().height+8,height=(vv?.height||innerHeight)-view.close.parentElement.getBoundingClientRect().height-24;menu.style.top=top+'px';menu.style.maxHeight=Math.max(80,height)+'px';input.scrollIntoView({block:'nearest'})};
 window.addEventListener('resize',resizeScaleMenu,{signal:events.signal});
 window.visualViewport?.addEventListener('resize',resizeScaleMenu,{signal:events.signal});
 view.scaleCleanup=()=>events.abort();
 wrap.append(scale,menu);actions.append(recipeFavoriteButton(meal),edit,wrap);header.append(title,actions,dismiss);view.content.append(header);
 return {title,scale};
}

function recipeLinkMessage(view,message){
 if(view.linkEdit)view.linkEdit.message=message;else view.linkNotice=message;
 renderRecipeViewer();
}
function beginRecipeLinkEdit(view,token){
 if(recipeViewer!==view)return;
 if(view.linkEdit){
  const draft=view.linkEdit,meal=meals.find(m=>String(m.id)===view.mealId);if(draft.step===token)return;
  if(!meal||!recipeAssociationItems(meal).steps.some(step=>step.token===token))return;
  draft.pending[draft.step]=draft.automatic?null:[...draft.selected];
  const saved=draft.pending[token],manual=validRecipeIngredientLinks(meal).find(link=>link.step===token);
  draft.step=token;draft.automatic=saved===null||saved===undefined&&!manual;
  draft.selected=new Set(saved===undefined?recipeIngredientMatches(meal).get(token)||[]:saved===null?recipeIngredientMatches({...meal,ingredientStepLinks:validRecipeIngredientLinks(meal).filter(link=>link.step!==token)}).get(token)||[]:saved);
  draft.message='';view.linkLayoutTransition=true;renderRecipeViewer();return;
 }
 const meal=meals.find(m=>String(m.id)===view.mealId);if(!meal)return;
 const items=recipeAssociationItems(meal);
 if(!items.steps.some(s=>s.token===token)){recipeLinkMessage(view,'This step repeats identically. Make it distinct in Edit Recipe before adding links.');return}
 cancelRecipeAdvance(view);view.cancelIngredientSync?.();
 for(const pane of view.content.querySelectorAll('.recipe-pane'))pane.scrollTo({top:pane.scrollTop,behavior:'instant'});
 const links=validRecipeIngredientLinks(meal),manual=links.find(l=>l.step===token);
 view.linkNotice='';view.linkEdit={pending:{},step:token,automatic:!manual,selected:new Set(recipeIngredientMatches(meal).get(token)||[]),originalLinks:JSON.stringify(links),content:JSON.stringify(cookingItemTokens(meal)),message:''};
 view.linkLayoutTransition=true;renderRecipeViewer();
}
function finishRecipeLinkEdit(save){
 const view=recipeViewer,draft=view?.linkEdit;if(!draft)return;
 const meal=meals.find(m=>String(m.id)===view.mealId);
 if(save){
  if(!meal||JSON.stringify(cookingItemTokens(meal))!==draft.content||JSON.stringify(validRecipeIngredientLinks(meal))!==draft.originalLinks){recipeLinkMessage(view,'The recipe changed while these links were being edited. Cancel and reopen the links to review the updated recipe.');return}
  draft.pending[draft.step]=draft.automatic?null:[...draft.selected];
  const links=validRecipeIngredientLinks(meal).filter(link=>!Object.hasOwn(draft.pending,link.step));
  for(const [step,ingredients]of Object.entries(draft.pending))if(ingredients!==null)links.push({step,ingredients});
  const validated=validRecipeIngredientLinks(meal,links);
  if(validated.length!==links.length){recipeLinkMessage(view,'These ingredient links are no longer valid. Cancel and reopen the links to review them.');return}
  if(JSON.stringify(validated)!==draft.originalLinks){
   const members=new Set(sharedRecipeMembers(meal));if([...members].some(copy=>JSON.stringify(validRecipeIngredientLinks(copy,validated))!==JSON.stringify(validated))){recipeLinkMessage(view,'Shared copies have different ingredients or instructions. Update their recipe content before saving shared step links.');return}
   try{localStorage.setItem('mealRotationDataV1',JSON.stringify({cats,active,meals:meals.map(m=>members.has(m)?{...m,ingredientStepLinks:validated}:m)}))}
   catch(e){recipeLinkMessage(view,'Ingredient links could not be saved. Your draft and previous saved recipe are unchanged. Free some browser storage and try again.');return}
   snapshot();assignSharedRecipeFields(meal,{ingredientStepLinks:validated});view.contentChanged=true;
  }
 }
 // Associations affect future instruction actions, never existing session marks.
 const matches=meal?recipeIngredientMatches(meal):new Map();
 view.syncMatches=matches;view.syncMatchSignature=meal?JSON.stringify([meal.ingredients,meal.instructions,meal.ingredientStepLinks]):'';
 const state=view.ingredientSyncState||(view.ingredientSyncState={suspended:false,lastStep:null,tokens:[]});
 state.lastStep=draft.step;state.tokens=matches.get(draft.step)||[];view.syncPinnedStep=draft.step;view.syncGeometryHold=true;view.syncWasEnabled=recipeGuidanceEnabled();view.syncRequested=false;
 view.linkEdit=null;view.linkLayoutTransition=true;renderRecipeViewer();
 const selected=[...view.content.querySelectorAll('.recipe-instructions-pane [data-cooking-token]')].find(el=>el.dataset.cookingToken===draft.step);selected?.focus({preventScroll:true});
}
function useAutomaticRecipeLinks(){
 const view=recipeViewer,draft=view?.linkEdit,meal=meals.find(m=>String(m.id)===view?.mealId);if(!draft||!meal)return;
 draft.automatic=true;draft.selected=new Set(recipeIngredientMatches({...meal,ingredientStepLinks:validRecipeIngredientLinks(meal).filter(l=>l.step!==draft.step)}).get(draft.step)||[]);draft.message='';renderRecipeViewer();view.cover.querySelector('.recipe-link-automatic')?.focus({preventScroll:true});
}
function clearRecipeLinkGestures(view){
 view.linkGestureEvents?.abort();view.linkGestureEvents=null;
 for(const timer of view.linkGestureTimers||[])clearTimeout(timer);view.linkGestureTimers=new Set();
}
function bindRecipeStepLongPress(view,button,token){
 if(!view.linkGestureEvents)view.linkGestureEvents=new AbortController();
 const signal=view.linkGestureEvents.signal;let timer=null,start=null,held=false,moved=false;
 const stop=()=>{clearTimeout(timer);view.linkGestureTimers?.delete(timer);timer=null};
 button.addEventListener('pointerdown',e=>{
  if(e.button!==0)return;stop();start={x:e.clientX,y:e.clientY};held=false;moved=false;
  timer=setTimeout(()=>{held=true;view.linkGestureTimers?.delete(timer);view.suppressLinkGestureClick=true;beginRecipeLinkEdit(view,token)},550);view.linkGestureTimers.add(timer);
 },{signal});
 button.addEventListener('pointermove',e=>{if(start&&Math.hypot(e.clientX-start.x,e.clientY-start.y)>10){moved=true;held=false;stop()}},{signal,passive:true});
 button.addEventListener('pointerup',e=>{
  stop();if(!start)return;start=null;
  if(held||moved){e.preventDefault();e.stopPropagation();view.suppressLinkGestureClick=true;if(held&&!moved)beginRecipeLinkEdit(view,token)}
  held=false;
 },{signal});
 button.addEventListener('pointerleave',()=>{stop();start=null;held=false},{signal});
 button.addEventListener('pointercancel',()=>{stop();start=null;held=false},{signal});
 button.addEventListener('contextmenu',e=>e.preventDefault(),{signal});
}
function buildRecipeLinkIngredient(view,item,meal,multiplier,session){
 const label=document.createElement('label');label.className='cooking-item recipe-link-ingredient';label.dataset.cookingToken=item.token;
 label.classList.toggle('cooking-complete',!!session?.ingredients.includes(item.token));
 const text=document.createElement('span');text.textContent=scaleRecipeIngredient(item.text,multiplier);
 if(syncIngredientHeading(item.text)){label.append(text);return label}
 const allowed=view.linkIngredientTokens.has(item.token),input=document.createElement('input');input.type='checkbox';input.checked=view.linkEdit.selected.has(item.token);input.disabled=!allowed;
 input.setAttribute('aria-label',text.textContent);if(!allowed)input.title='Make repeated ingredient lines distinct in Edit Recipe before linking them.';
 input.onchange=()=>{if(input.checked)view.linkEdit.selected.add(item.token);else view.linkEdit.selected.delete(item.token);view.linkEdit.automatic=false;view.linkEdit.message='';view.cover.querySelector('.recipe-link-edit-bar [role="status"]')?.remove();const automatic=view.cover.querySelector('.recipe-link-automatic');automatic?.setAttribute('aria-pressed','false')};
 label.append(input,text);return label;
}
function renderRecipeLinkBar(view){
 view.cover.querySelector('.recipe-link-edit-bar')?.remove();if(!view.linkEdit)return;
 const bar=document.createElement('div');bar.className='recipe-link-edit-bar';bar.setAttribute('role','toolbar');bar.setAttribute('aria-label','Edit ingredient links');
 for(const [kind,label,save] of [['save','Save ingredient links',true],['close','Cancel ingredient links',false]]){
  const b=document.createElement('button');b.type='button';b.className='recipe-header-icon';setRecipeToolbarIcon(b,kind,label);b.onclick=()=>finishRecipeLinkEdit(save);bar.append(b);
  if(save){const automatic=document.createElement('button');automatic.type='button';automatic.className='recipe-link-automatic';automatic.textContent='Use Automatic Matching';automatic.setAttribute('aria-pressed',String(view.linkEdit.automatic));automatic.onclick=useAutomaticRecipeLinks;bar.append(automatic)}
 }
 if(view.linkEdit.message){const message=document.createElement('p');message.className='recipe-link-message';message.setAttribute('role','status');message.textContent=view.linkEdit.message;message.style.cssText='position:absolute;bottom:100%;left:0;right:0;margin:0;padding:8px 20px;background:#fff;border-top:1px solid #dce2e9';bar.append(message)}
 view.cover.append(bar);
}
function restoreRecipeLinkViewport(view,ingredientsPane,instructionsPane,coverScroll,paneScroll){
 if(!view.linkLayoutTransition)return;view.linkLayoutTransition=false;
 const split=view.cover.classList.contains('recipe-split');
 if(split&&(paneScroll[0]||0)>ingredientsPane.scrollHeight-ingredientsPane.clientHeight){
  let tail=ingredientsPane.querySelector('.recipe-link-ingredient-tail');if(!tail){tail=document.createElement('div');tail.className='recipe-link-ingredient-tail';tail.setAttribute('aria-hidden','true');ingredientsPane.append(tail)}
  const trial=Math.max(view.linkIngredientTailSpace||0,ingredientsPane.clientHeight);tail.style.height=trial+'px';view.linkIngredientTailSpace=Math.max(view.linkIngredientTailSpace||0,Math.ceil(trial+(paneScroll[0]||0)+ingredientsPane.clientHeight-ingredientsPane.scrollHeight));tail.style.height=view.linkIngredientTailSpace+'px';
 }
 const pane=split?instructionsPane:view.cover;
 const desired=pane===view.cover?coverScroll:paneScroll[1]||0;
 if(desired>pane.scrollHeight-pane.clientHeight){
  let tail=instructionsPane.querySelector('.recipe-link-scroll-tail');if(!tail){tail=document.createElement('div');tail.className='recipe-link-scroll-tail';tail.setAttribute('aria-hidden','true');instructionsPane.append(tail)}
  const trial=Math.max(view.linkTailSpace||0,pane.clientHeight);tail.style.height=trial+'px';view.linkTailSpace=Math.max(view.linkTailSpace||0,Math.ceil(trial+desired+pane.clientHeight-pane.scrollHeight));tail.style.height=view.linkTailSpace+'px';
 }
 ingredientsPane.scrollTop=paneScroll[0]||0;instructionsPane.scrollTop=paneScroll[1]||0;view.cover.scrollTop=coverScroll;
}

function needsTweakingIconSvg(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6m0 4h.01"/></svg>'}
function needsTweakingIndicator(meal,updated=null){
 if(meal.needsTweaking!==true)return null;
 const button=document.createElement('button');button.type='button';button.className='needs-tweaking-icon';button.innerHTML=needsTweakingIconSvg();button.title='Needs Adjusting: '+(meal.name||'Recipe');button.setAttribute('aria-label',button.title);
 // Keep taps and swipes entirely separate from the recipe-name/row gestures.
 for(const event of ['pointerdown','pointerup','touchstart','touchend','dblclick'])button.addEventListener(event,e=>e.stopPropagation());
 button.onclick=e=>{e.preventDefault();e.stopPropagation();const current=meals.find(m=>String(m.id)===String(meal.id));if(current?.needsTweaking===true)openNeedsTweaking(current,updated)};return button;
}
function appendNeedsTweakingIndicator(parent,meal,updated=null){const icon=needsTweakingIndicator(meal,updated);if(icon)parent.append(icon)}
function refreshNeedsTweakingViews(updated){
 renderList();updated?.();
 const view=recipeViewer;if(!view)return;
 // Tracking changes do not invalidate an occurrence, its progress, or its scale.
 view.contentChanged=true;renderRecipeViewer();
}
// Existing records are group memberships. Only linkGroup proves shared identity;
// linkedMealIds are serving relationships, and names/source URLs are not identity.
const RECIPE_MEMBERSHIP_FIELDS=new Set(['id','cat','rotation','linkGroup','rotationPromotionPriority']);
function sharedRecipeMembers(meal,library=meals){return meal?library.filter(m=>String(m.id)===String(meal.id)||!!meal.linkGroup&&m.linkGroup===meal.linkGroup):[]}
function sharedRecipeChanges(before,after){const patch={};for(const key of new Set([...Object.keys(before),...Object.keys(after)]))if(!RECIPE_MEMBERSHIP_FIELDS.has(key)&&JSON.stringify(before[key])!==JSON.stringify(after[key]))patch[key]=after[key];return patch}
function assignSharedRecipeFields(meal,patch,library=meals){
 const members=sharedRecipeMembers(meal,library);for(const record of members)for(const [key,value]of Object.entries(patch)){if(RECIPE_MEMBERSHIP_FIELDS.has(key))continue;if(value===undefined)delete record[key];else record[key]=JSON.parse(JSON.stringify(value))}return members;
}
function selectedSharedRecipeIds(ids,library=meals){const selected=new Set(ids.map(String));for(const record of library)if(selected.has(String(record.id)))for(const peer of sharedRecipeMembers(record,library))selected.add(String(peer.id));return [...selected]}
function recipeIdentityCount(ids){const selected=new Set(ids.map(String));return new Set(meals.filter(m=>selected.has(String(m.id))).map(m=>m.linkGroup?'shared:'+m.linkGroup:'recipe:'+String(m.id))).size}
// Shared group-name validation and the same append-to-cats operation as Add group.
function validateNewMealGroupName(value,groups=cats){
 const name=String(value||'').trim();if(!name)throw Error('Enter a group name.');if(groups.some(cat=>cat.toLocaleLowerCase()===name.toLocaleLowerCase()))throw Error('A group with this name already exists.');
 return name;
}
function createMealGroup(value){
 const name=validateNewMealGroupName(value);
 const before=captureState(),next=[...cats,name];localStorage.setItem('mealRotationDataV1',JSON.stringify({cats:next,active,meals}));cats=next;snapshot(before);return name;
}

function assignRecipeTweaking(meal,marked,note=''){
 assignSharedRecipeFields(meal,{needsTweaking:marked?true:undefined,needsTweakingNote:marked?String(note).trim():undefined})
}
let needsTweakingRemovalPending=false;
async function confirmNeedsTweakingRemoval(description='This removes only the Needs Adjusting status and its note. Recipes will not be deleted, and rotation positions will not change.'){
 if(needsTweakingRemovalPending)return false;
 needsTweakingRemovalPending=true;
 const focus=document.activeElement,inert=[...document.body.children].map(el=>[el,el.inert]);inert.forEach(([el])=>el.inert=true);
 try{return await appDialog('Remove Needs Adjusting?',null,'tracking-remove',[],description)===true}
 finally{needsTweakingRemovalPending=false;for(const [el,was]of inert)if(el.isConnected)el.inert=was;if(focus?.isConnected)focus.focus({preventScroll:true})}
}
async function removeRecipeNeedsTweaking(meal,updated=null,onRemoved=null){
 if(recipeViewer?.linkEdit){recipeLinkMessage(recipeViewer,'Save or cancel ingredient links before removing Needs Adjusting.');return false}
 if(!meals.includes(meal)||!await confirmNeedsTweakingRemoval()||!meals.includes(meal))return false;
 snapshot();assignRecipeTweaking(meal,false);persist();onRemoved?.();refreshNeedsTweakingViews(updated);return true;
}
function recipeTweakingAction(text,action){const button=document.createElement('button');button.type='button';button.className='recipe-tweaking-action';button.textContent=text;button.onclick=e=>{e.preventDefault();e.stopPropagation();action()};return button}
function recipeTweakingEditAction(action){const button=recipeTweakingAction('Edit note',action);button.classList.add('recipe-tweaking-edit');const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');svg.innerHTML=appIconSvg.rename;button.prepend(svg);return button}
function recipeTweakingTrash(action){const button=document.createElement('button');button.type='button';button.className='recipe-tweaking-trash';setIconButton(button,'delete','Remove Needs Adjusting');button.onclick=e=>{e.preventDefault();e.stopPropagation();action()};return button}
function recipeTweakingHeading(meal,remove,id=null){
 const header=document.createElement('div');header.className='recipe-tweaking-header';
 const heading=document.createElement('div');heading.className='recipe-tweaking-heading';if(id)heading.id=id;
 if(meal.needsTweaking===true)heading.innerHTML=needsTweakingIconSvg();const title=document.createElement('span');title.textContent='Needs Adjusting';heading.append(title);header.append(heading);
 if(meal.needsTweaking===true)header.append(recipeTweakingTrash(remove));return header;
}
function renderRecipeTweakingStatus(view,meal){
 if(meal.needsTweaking!==true)return;
 const tab=view.activeTab,status=document.createElement('section');status.className='recipe-tweaking-status';status.setAttribute('aria-label','Needs Adjusting');
 const header=recipeTweakingHeading(meal,()=>removeRecipeNeedsTweaking(meal));status.append(header);
 let note=null;if(typeof meal.needsTweakingNote==='string'&&meal.needsTweakingNote.trim()){note=document.createElement('p');note.className='recipe-tweaking-note';note.textContent=meal.needsTweakingNote;status.append(note)}
 const actions=document.createElement('div');actions.className='recipe-tweaking-actions';actions.append(recipeTweakingEditAction(()=>openNeedsTweaking(meal,null,true)));
 const toggle=document.createElement('button');toggle.type='button';toggle.className='recipe-tweaking-toggle';
 function display(){const collapsed=tab.needsAdjustingCollapsed===true;status.classList.toggle('recipe-tweaking-collapsed',collapsed);if(note)note.hidden=collapsed;header.querySelector('.recipe-tweaking-trash').hidden=collapsed;actions.hidden=collapsed;setRecipeToolbarIcon(toggle,collapsed?'expand':'collapse',collapsed?'Expand Needs Adjusting note':'Collapse Needs Adjusting note');toggle.setAttribute('aria-expanded',String(!collapsed));(collapsed?header:actions).append(toggle)}
 toggle.onclick=e=>{e.preventDefault();e.stopPropagation();tab.needsAdjustingCollapsed=tab.needsAdjustingCollapsed!==true;display()};
 status.append(actions);display();view.content.append(status);
}
// Display preferences do not alter recipe tasks or dated occurrence completions.
const MAKE_AHEAD_DISPLAY_KEY='mealRotationMakeAheadDisplayV1';
let makeAheadDisplayPrefs={showMakeAheadReminders:true,showCompletedToday:false};
try{const saved=JSON.parse(localStorage.getItem(MAKE_AHEAD_DISPLAY_KEY)||'null');for(const key of Object.keys(makeAheadDisplayPrefs))if(typeof saved?.[key]==='boolean')makeAheadDisplayPrefs[key]=saved[key]}catch(e){}
function saveMakeAheadDisplayPrefs(){try{localStorage.setItem(MAKE_AHEAD_DISPLAY_KEY,JSON.stringify(makeAheadDisplayPrefs))}catch(e){}}
function populateMakeAheadSetting(parent){
 const label=document.createElement('label');label.className='settings-display-option';const check=document.createElement('input');check.type='checkbox';check.checked=makeAheadDisplayPrefs.showMakeAheadReminders;
 check.onchange=()=>{makeAheadDisplayPrefs.showMakeAheadReminders=check.checked;saveMakeAheadDisplayPrefs();renderList()};label.append(check,document.createTextNode('Show Make Ahead Reminders'));parent.append(label);
}
function setMakeAheadComplete(item,checked){
 const plan=mealPlans.find(plan=>plan.id===item.plan.id);if(!plan)return;
 if(!scheduledMakeAheadTasks().some(current=>current.plan.id===plan.id&&current.key===item.key)){renderTodayTodo();return}
 snapshot();plan.makeAheadChecks={...(plan.makeAheadChecks||{}),[item.key]:checked};saveActiveMealPlan();
 for(const row of document.querySelectorAll('[data-make-ahead-key]')){const current=mealPlans.find(plan=>String(plan.id)===row.dataset.planId),complete=current?makeAheadTaskComplete(current,row.dataset.makeAheadKey):false;row.querySelector('input[type="checkbox"]').checked=complete;row.classList.toggle('make-ahead-complete',complete)}if(allMealsActive||rotationWeekOffset)renderList();else renderTodayTodo();
}
const todoCollapsed={0:false,1:false};
function renderTodayTodo(provided=null){
 const old=document.getElementById('todaysTodo'),visibility=document.getElementById('todoVisibilityControl'),header=document.querySelector('#list>.rotation-compact-header');
 if(!header||!showTop||allMealsActive||groceryTabActive||!makeAheadDisplayPrefs.showMakeAheadReminders){old?.remove();visibility?.remove();return}
 const today=cookingLocalDate(new Date()),start=cookingPlanningWeekStart();start.setDate(start.getDate()+7);const end=new Date(start);end.setDate(end.getDate()+7);
 const seen=new Set(),items=(provided||scheduledMakeAheadTasks()).filter(item=>{
  const id=JSON.stringify([item.plan.id,item.key]);if(!makeAheadTaskVisible(item,today)||seen.has(id))return false;
  if(rotationWeekOffset?item.plan.id!==activePlanId||item.scheduled<cookingLocalDate(start)||item.scheduled>=cookingLocalDate(end):item.due>today)return false;
  seen.add(id);return true;
 }).sort((a,b)=>Number(a.complete)-Number(b.complete)||a.due.localeCompare(b.due));
 if(!items.length){old?.remove();visibility?.remove();return}
 const section=old||document.createElement('section');section.id='todaysTodo';section.setAttribute('aria-labelledby','todaysTodoHeading');
 const heading=section.querySelector('.today-todo-heading')||document.createElement('div');heading.className='today-todo-heading';
 const title=heading.querySelector('h3')||document.createElement('h3');title.id='todaysTodoHeading';title.textContent=rotationWeekOffset?'Next Week’s To-Do':"Today's To-Do";
 const eye=heading.querySelector('.todo-completed-toggle')||visibility?.querySelector('button')||document.createElement('button');eye.type='button';eye.className='iconbtn todo-completed-toggle';eye.setAttribute('aria-pressed',String(makeAheadDisplayPrefs.showCompletedToday));eye.title=makeAheadDisplayPrefs.showCompletedToday?'Hide completed tasks':'Show completed tasks';eye.setAttribute('aria-label',eye.title);eye.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>'+(makeAheadDisplayPrefs.showCompletedToday?'':'<path d="m3 3 18 18"/>')+'</svg>';
 eye.onclick=event=>{event.preventDefault();event.stopPropagation();makeAheadDisplayPrefs.showCompletedToday=!makeAheadDisplayPrefs.showCompletedToday;saveMakeAheadDisplayPrefs();renderTodayTodo();document.querySelector('.todo-completed-toggle')?.focus({preventScroll:true})};
 const shown=items.filter(item=>!item.complete||makeAheadDisplayPrefs.showCompletedToday);
 if(!shown.length){const control=visibility||document.createElement('div');control.id='todoVisibilityControl';control.replaceChildren(eye);old?.remove();header.after(control);return}
 const body=document.createElement('div');body.id='todoTaskItems';body.hidden=todoCollapsed[rotationWeekOffset];
 const collapse=heading.querySelector('.todo-collapse-toggle')||document.createElement('button');collapse.type='button';collapse.className='iconbtn todo-collapse-toggle';collapse.setAttribute('aria-controls',body.id);
 const refresh=()=>{body.hidden=todoCollapsed[rotationWeekOffset];collapse.setAttribute('aria-expanded',String(!body.hidden));setRecipeToolbarIcon(collapse,body.hidden?'expand':'collapse',body.hidden?'Expand to-do tasks':'Collapse to-do tasks')};
 collapse.onclick=()=>{todoCollapsed[rotationWeekOffset]=!todoCollapsed[rotationWeekOffset];refresh()};refresh();heading.replaceChildren(collapse,title,eye);section.replaceChildren(heading,body);
 for(const item of shown){const row=makeAheadReminderRow(item,true);if(rotationWeekOffset){const due=document.createElement('small');due.className='make-ahead-due';due.textContent='Due '+parseCookingLocalDate(item.due).toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric',year:'numeric'});row.append(due)}body.append(row)}
 visibility?.remove();if(!old)header.after(section);
}
let makeAheadDayTimer=null,makeAheadLocalDay=null;
function syncMakeAheadLocalDay(){
 clearTimeout(makeAheadDayTimer);if(document.hidden)return;
 const now=new Date(),today=cookingLocalDate(now);if(today!==makeAheadLocalDay){makeAheadLocalDay=today;if((allMealsActive||rotationWeekOffset)&&showTop&&!groceryTabActive&&editId===null)renderList();else renderTodayTodo()}
 const midnight=new Date(now);midnight.setHours(24,0,0,50);makeAheadDayTimer=setTimeout(syncMakeAheadLocalDay,Math.max(100,midnight-now));
}
window.addEventListener('focus',syncMakeAheadLocalDay);window.addEventListener('pageshow',syncMakeAheadLocalDay);window.addEventListener('pagehide',()=>clearTimeout(makeAheadDayTimer));document.addEventListener('visibilitychange',syncMakeAheadLocalDay);

// Explicit recipe tasks; completion belongs to a dated scheduled occurrence.
function validMakeAheadLead(task){return Number.isFinite(task.daysBefore)&&task.daysBefore>=0&&task.daysBefore<=36600&&(task.hoursBefore===undefined||Number.isFinite(task.hoursBefore)&&task.hoursBefore>=0&&task.hoursBefore<=878400)}
function recipeMakeAheadTasks(meal){return (Array.isArray(meal.makeAheadTasks)?meal.makeAheadTasks:[]).filter(t=>t&&typeof t.id==='string'&&typeof t.description==='string'&&t.description.trim()&&validMakeAheadLead(t))}
function makeAheadTiming(days,hours){return hours!==undefined?hours===0?'Same day':hours+' hour'+(hours===1?'':'s')+' before':days===0?'Same day':days===1?'1 day before':days+' days before'}
function buildMakeAheadEditor(meal,before=$('editorNotesSection')){
 const group=mealEditorSubsection('ahead','Make Ahead','recipeMakeAhead',meal),box=group.details,body=group.content;body.classList.add('make-ahead-editor');
 const changed=()=>box.dispatchEvent(new Event('change',{bubbles:true}));
 function taskRow(task={},after=null){
  const row=document.createElement('div');row.className='make-ahead-task-editor';row.dataset.taskId=task.id||'prep-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8);
  const description=document.createElement('input');description.type='text';description.className='make-ahead-description';description.placeholder='Preparation task';description.setAttribute('aria-label','Preparation task');description.value=task.description||'';
  const timing=document.createElement('div');timing.className='make-ahead-lead';
  const number=document.createElement('input');number.type='number';number.inputMode='decimal';number.min='0';number.step='any';number.className='make-ahead-days';number.setAttribute('aria-label','Preparation lead time');number.value=String(task.hoursBefore??task.daysBefore??0);
  const unit=document.createElement('input');unit.type='hidden';unit.value=task.hoursBefore!==undefined?'hours':'days';
  const units=document.createElement('div');units.className='meal-editor-segmented';units.setAttribute('role','group');units.setAttribute('aria-label','Preparation lead time unit');
  for(const [value,text]of [['hours','Hours'],['days','Days']]){const option=document.createElement('button');option.type='button';option.textContent=text;option.dataset.leadUnit=value;option.setAttribute('aria-pressed',String(unit.value===value));option.onclick=()=>{unit.value=value;for(const button of units.querySelectorAll('button'))button.setAttribute('aria-pressed',String(button===option));changed()};units.append(option)}
  timing.append(number,unit,units);const hint=document.createElement('small');hint.className='muted make-ahead-timing-hint';hint.hidden=validMakeAheadLead(task)||task.id===undefined;hint.textContent=hint.hidden?'':'Saved lead time: '+String(task.hoursBefore??task.daysBefore)+' '+(task.hoursBefore!==undefined?'hours':'days')+' (retained until edited).';
  const initial={number:number.value,unit:unit.value},untouched=()=>number.value===initial.number&&unit.value===initial.unit;
  row.readDraft=()=>{const record={...task,id:row.dataset.taskId,description:description.value.trim()};if(!untouched()||task.id===undefined){delete record.hoursBefore;record.daysBefore=unit.value==='days'?Number(number.value):0;if(unit.value==='hours')record.hoursBefore=Number(number.value)}return record};
  row.validDraft=()=>!description.value.trim()||task.id!==undefined&&untouched()||number.value.trim()!==''&&validMakeAheadLead(row.readDraft())&&(unit.value!=='hours'||Number(number.value)>0);
  const remove=document.createElement('button');remove.type='button';remove.className='meal-editor-inline-icon';setIconButton(remove,'delete','Remove preparation task');remove.onclick=()=>{row.remove();if(!body.querySelector('.make-ahead-task-editor'))taskRow();changed()};
  const add=document.createElement('button');add.type='button';add.className='meal-editor-inline-icon';setIconButton(add,'add','Add preparation task');add.onclick=()=>{const next=taskRow({},row);next.querySelector('input').focus({preventScroll:true});changed()};timing.append(add);
  row.append(description,remove,timing,hint);if(after)after.after(row);else body.append(row);return row;
 }
 const saved=Array.isArray(meal.makeAheadTasks)?meal.makeAheadTasks:[];saved.filter(t=>t&&typeof t==='object').forEach(task=>taskRow(task));if(!saved.length)taskRow();
 before.before(box);
 box.readDraft=()=>[...body.querySelectorAll('.make-ahead-task-editor')].map(row=>row.readDraft()).filter(t=>t.description);
 box.validDraft=()=>[...body.querySelectorAll('.make-ahead-task-editor')].every(row=>row.validDraft());return box;
}
function makeAheadWeekStart(){const plan=mealPlans.find(p=>p.id===activePlanId);return parseCookingLocalDate(plan?.rotationCalendar?.weekStart)||cookingPlanningWeekStart()}
function makeAheadTaskComplete(plan,key){
 if(Object.hasOwn(plan.makeAheadChecks||{},key))return plan.makeAheadChecks[key]===true;
 const target=JSON.parse(key);return Object.entries(plan.makeAheadChecks||{}).some(([saved,checked])=>{try{const parts=JSON.parse(saved);return checked&&(parts[2]==='preview'||target[2]==='preview')&&parts[0]===target[0]&&parts[1]===target[1]&&parts[3]===target[3]}catch(_){return false}});
}
function scheduledMakeAheadTasks(includeUpcoming=true,upcoming=null){
 const start=cookingPlanningWeekStart(),rows=[],seen=new Set(),current=mealPlans.map(plan=>({plan:plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan,entries:null}));
 for(const source of current.concat(includeUpcoming?(upcoming||previewNextWeekPlans()):[])){
  const plan=source.plan,entries=source.entries||getDisplayedWeekdayMealsForPlan(plan),calendar=rotationCalendarForPlan(plan,entries),real=mealPlans.find(item=>item.id===plan.id)||plan;
  for(const entry of entries){const occurrence=rotationOccurrenceKey({...entry,planId:plan.id}),scheduled=parseCookingLocalDate(calendar.occurrences?.[occurrence])||cookingDateInWeek(entry.day,parseCookingLocalDate(calendar.weekStart)||start);if(!scheduled)continue;
   for(const task of recipeMakeAheadTasks(entry.meal)){
    const due=makeAheadDueDate(scheduled,task);
    const key=JSON.stringify([occurrence,cookingLocalDate(scheduled),source.preview?'preview':calendar.assignedAt?.[occurrence]||'',task.id]),identity=JSON.stringify([plan.id,occurrence,cookingLocalDate(scheduled),task.id]);if(seen.has(identity))continue;seen.add(identity);
    rows.push({plan:real,entry,task,key,due:cookingLocalDate(due),scheduled:cookingLocalDate(scheduled),complete:makeAheadTaskComplete(real,key)});
   }
  }
 }
 for(const plan of mealPlans)for(const item of plan.makeAheadPending||[]){if(!item||typeof item.key!=='string'||!item.entry?.meal||!item.task)continue;const parts=JSON.parse(item.key),identity=JSON.stringify([plan.id,parts[0],item.scheduled,item.task.id]);if(seen.has(identity)||makeAheadTaskComplete(plan,item.key))continue;seen.add(identity);rows.push({...item,plan,complete:false})}
 return rows;
}
function retainDueMakeAheadTasks(){
 const today=cookingLocalDate(new Date());for(const item of scheduledMakeAheadTasks()){
  if(item.complete||item.due>today)continue;const plan=mealPlans.find(plan=>plan.id===item.plan.id);if(!plan)continue;
  const pending=(plan.makeAheadPending||[]).filter(saved=>!makeAheadTaskComplete(plan,saved.key));
  if(!pending.some(saved=>saved.key===item.key))pending.push({key:item.key,due:item.due,scheduled:item.scheduled,task:{...item.task},entry:{day:item.entry.day,cat:item.entry.cat,meal:{id:item.entry.meal.id,name:item.entry.meal.name}}});plan.makeAheadPending=pending;
 }
}
function makeAheadDueDate(scheduled,task){
 const due=new Date(scheduled);if(task.hoursBefore!==undefined)due.setTime(due.getTime()-task.hoursBefore*3600000);else if(Number.isInteger(task.daysBefore))due.setDate(due.getDate()-task.daysBefore);else due.setTime(due.getTime()-task.daysBefore*86400000);return due;
}
function editPreparationTask(item){
 if(document.querySelector('.preparation-task-dialog'))return;
 const meal=meals.find(meal=>String(meal.id)===String(item.entry.meal.id)),task=meal&&recipeMakeAheadTasks(meal).find(task=>task.id===item.task.id);if(!task)return;
 const baseline=JSON.stringify(task),d=recipeBulkDialog('Edit preparation task'),mount=document.createElement('div');d.overlay.classList.add('preparation-task-dialog');d.panel.append(mount);
 const editor=buildMakeAheadEditor({...meal,makeAheadTasks:[{...task}]},mount);editor.id='preparationTaskDraft';editor.open=true;editor.querySelector('summary').hidden=true;mount.remove();
 editor.querySelectorAll('[aria-label="Remove preparation task"],[aria-label="Add preparation task"]').forEach(button=>button.hidden=true);
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');const actions=document.createElement('div');actions.className='meal-unified-actions';
 const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Save preparation task');setIconButton(cancel,'cancel','Cancel preparation edit');cancel.onclick=d.close;let saving=false;
 save.onclick=()=>{if(saving)return;const draft=editor.readDraft()[0];if(!draft||!editor.validDraft()){error.textContent='Enter a task and a valid lead time.';return}
  const current=meals.find(record=>String(record.id)===String(meal.id)),existing=current&&recipeMakeAheadTasks(current).find(record=>record.id===task.id);
  if(!existing||JSON.stringify(existing)!==baseline){error.textContent='This reminder changed. Cancel and reopen it to edit the latest version.';return}
  saving=true;try{applyRecipeBulk([String(current.id)],{}, {render:false,viewerEdit:{sourceId:String(current.id),fields:{makeAheadTasks:current.makeAheadTasks.map(record=>record?.id===task.id?{...draft,id:task.id}:record)},owner:'preparation:'+current.id+':'+task.id}});d.close();renderList();const parent=document.querySelector('[data-make-ahead-recipe]');if(parent){const record=meals.find(meal=>String(meal.id)===parent.dataset.makeAheadRecipe);parent.remove();if(record)openMakeAheadTasks(record)}}catch(e){error.textContent='Reminder could not be saved: '+e.message}finally{saving=false}
 };
 actions.append(save,cancel);d.panel.append(error,actions);fitOneTimeMealViewport(d.overlay,d.panel);editor.querySelector('input')?.focus({preventScroll:true});
}
function bindPreparationTaskPress(row,item){
 let timer=null,start=null,held=false;const stop=()=>{clearTimeout(timer);timer=null};
 row.addEventListener('pointerdown',event=>{if(event.button!==0)return;stop();held=false;start={x:event.clientX,y:event.clientY};timer=setTimeout(()=>{held=true;editPreparationTask(item)},550)});
 row.addEventListener('pointermove',event=>{if(start&&Math.hypot(event.clientX-start.x,event.clientY-start.y)>10){stop();start=null}});
 for(const event of ['pointerup','pointercancel','pointerleave'])row.addEventListener(event,()=>{stop();start=null});
 row.addEventListener('click',event=>{if(held){event.preventDefault();event.stopImmediatePropagation();held=false}},true);
 row.addEventListener('contextmenu',event=>event.preventDefault());
}
function makeAheadReminderRow(item,today=false){
 const label=document.createElement('label');label.className='make-ahead-reminder'+(item.complete?' make-ahead-complete':'');label.dataset.makeAheadKey=item.key;label.dataset.planId=String(item.plan.id);const check=document.createElement('input');check.type='checkbox';check.className='check';check.checked=item.complete;
 const text=document.createElement('span');text.textContent=item.task.description+' · for '+item.entry.day+"'s "+(item.entry.meal.name||'meal')+(today?' · '+item.plan.name:'');check.setAttribute('aria-label',text.textContent);
 check.onchange=()=>setMakeAheadComplete(item,check.checked);label.append(check,text);bindPreparationTaskPress(label,item);return label;
}
function makeAheadTaskVisible(item,today=cookingLocalDate(new Date())){return typeof item.scheduled==='string'&&item.scheduled>=today}
function makeAheadCardDate(item){return item.due}
function appendMakeAheadDay(card,day,rows,start=makeAheadWeekStart()){
 const due=cookingLocalDate(cookingDateInWeek(day,start)),today=cookingLocalDate(new Date());for(const item of rows.filter(item=>makeAheadTaskVisible(item,today)&&makeAheadCardDate(item,today)===due))card.append(makeAheadReminderRow(item));
}
function makeAheadIndicator(meal){if(!makeAheadDisplayPrefs.showMakeAheadReminders||!recipeMakeAheadTasks(meal).length)return null;const b=document.createElement('button');b.type='button';b.className='recipe-personal-icon';setRecipeToolbarIcon(b,'prep','Make ahead: '+(meal.name||'Recipe'));b.onclick=e=>{e.preventDefault();e.stopPropagation();openMakeAheadTasks(meal)};for(const event of ['pointerdown','pointerup','touchstart','touchend','dblclick'])b.addEventListener(event,e=>e.stopPropagation());return b}
function openMakeAheadTasks(meal){
 const shade=document.createElement('div');shade.className='recipe-timer-dialog';shade.setAttribute('role','dialog');shade.setAttribute('aria-label','Make ahead: '+meal.name);shade.dataset.makeAheadRecipe=String(meal.id);const panel=document.createElement('div'),heading=document.createElement('strong');heading.textContent=meal.name||'Make ahead';panel.append(heading);
 const rows=scheduledMakeAheadTasks().filter(item=>String(item.entry.meal.id)===String(meal.id)&&makeAheadTaskVisible(item));if(rows.length)for(const item of rows){const line=makeAheadReminderRow(item),date=document.createElement('small');date.textContent=item.due+' · '+item.plan.name;line.append(date);panel.append(line)}else for(const task of recipeMakeAheadTasks(meal)){const p=document.createElement('p');p.textContent=task.description+' · '+makeAheadTiming(task.daysBefore,task.hoursBefore);panel.append(p)}
 const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close make ahead');close.onclick=()=>shade.remove();panel.append(close);shade.append(panel);shade.onclick=e=>{if(e.target===shade)shade.remove()};shade.onkeydown=e=>{if(e.key==='Escape')shade.remove()};document.body.append(shade);close.focus({preventScroll:true});
}

function buildRecipeTweakingEditor(meal){
 const control=document.createElement('section');control.id='editorNeedsTweaking';control.className='meal-editor-adjusting';
 const row=document.createElement('div');row.className='meal-editor-adjusting-row';const label=document.createElement('label');label.className='meal-checkbox-option';
 const state=document.createElement('input');state.type='checkbox';state.id='editNeedsTweaking';state.checked=meal.needsTweaking===true;label.append(state,document.createTextNode('Needs Adjusting'));
 const note=document.createElement('textarea');note.id='editNeedsTweakingNote';note.className='editor-tweaking-note';note.value=typeof meal.needsTweakingNote==='string'?meal.needsTweakingNote:'';note.placeholder='What would you change? (optional)';note.setAttribute('aria-label','Needs Adjusting note');
 const toggle=document.createElement('button');toggle.type='button';toggle.className='meal-editor-note-toggle';toggle.setAttribute('aria-label','Expand or collapse adjustment note');toggle.setAttribute('aria-controls',note.id);toggle.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
 let expanded=state.checked;
 const refresh=()=>{toggle.hidden=!state.checked;note.hidden=!state.checked||!expanded;toggle.setAttribute('aria-expanded',String(state.checked&&expanded));control.dispatchEvent(new Event('input',{bubbles:true}))};
 toggle.onclick=()=>{expanded=!expanded;refresh()};
 state.onchange=()=>{
  if(state.checked){expanded=true;refresh();return}
  if(!note.value.trim()){refresh();return}
  state.checked=true;refresh();const dialog=recipeBulkDialog('Uncheck Needs Adjusting?',()=>state);
  const text=document.createElement('p');text.textContent='Keep the adjustment note for later, or delete it?';dialog.panel.append(text);
  const actions=document.createElement('div');actions.className='meal-unified-actions';
  for(const [title,clear]of [['Keep note',false],['Delete note',true]]){const button=document.createElement('button');button.type='button';button.className='smallbtn';button.textContent=title;button.onclick=()=>{state.checked=false;if(clear)note.value='';expanded=false;refresh();dialog.close()};actions.append(button)}
  const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close adjustment confirmation');close.onclick=dialog.close;actions.append(close);dialog.panel.append(actions);actions.firstElementChild.focus({preventScroll:true});
 };
 row.append(label,toggle);control.append(row,note);refresh();$('rotation').closest('label').before(control);
}
function openNeedsTweaking(meal,updated=null,editing=false){
 if(document.getElementById('needsTweakingDialog'))return;
 // Closing an editor can restore cloned records before the original icon tap runs.
 meal=meals.find(current=>String(current.id)===String(meal?.id));if(!meal)return;
 if(recipeViewer?.linkEdit){recipeLinkMessage(recipeViewer,'Save or cancel ingredient links before editing Needs Adjusting.');return}
 const focus=document.activeElement,shade=document.createElement('div');shade.id='needsTweakingDialog';shade.style.cssText='position:fixed;inset:0;z-index:35000;background:#0008;display:flex;align-items:center;justify-content:center;padding:18px';
 const panel=document.createElement('section');panel.className='recipe-tweaking-popup';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-labelledby','needsTweakingTitle');panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:18px;width:100%;max-width:480px;max-height:85dvh;overflow:auto;box-shadow:0 12px 36px #0003';
 const recipe=document.createElement('p');recipe.textContent=meal.name||'Recipe';recipe.style.cssText='margin:2px 0 8px;color:#65717e;overflow-wrap:anywhere;font-size:14px';
 const label=document.createElement('label');label.htmlFor='needsTweakingNote';label.textContent='What would you change? (optional)';
 const field=document.createElement('textarea');field.id='needsTweakingNote';field.rows=4;field.value=typeof meal.needsTweakingNote==='string'?meal.needsTweakingNote:'';field.placeholder='Needs Adjusting';field.style.cssText='display:block;width:100%;resize:vertical;min-height:100px;margin:6px 0 10px;border:1px solid #ccc;border-radius:9px;padding:10px;font:inherit;font-size:16px;background:#fff;color:#242424';
 const status=document.createElement('p');status.setAttribute('role','status');status.style.cssText='margin:0;color:#825a13;font-size:14px';
 const inert=[...document.body.children].map(el=>[el,el.inert]);for(const [el]of inert)el.inert=true;
 const close=()=>{shade.remove();for(const [el,was]of inert)if(el.isConnected)el.inert=was;if(focus?.isConnected)focus.focus({preventScroll:true})};
 function draw(edit){
  panel.replaceChildren(recipeTweakingHeading(meal,()=>removeRecipeNeedsTweaking(meal,updated,close),'needsTweakingTitle'),recipe);
  const actions=document.createElement('div');
  if(edit){
   panel.append(label,field,status);actions.className='meal-unified-actions';actions.style.marginTop='8px';
   for(const [kind,text,save]of [['save','Save Needs Adjusting',true],['cancel','Cancel Needs Adjusting',false]]){const button=document.createElement('button');button.type='button';setIconButton(button,kind,text);button.onclick=()=>{
    if(!save){close();return}
    if(!meals.includes(meal)){status.textContent='This recipe changed. Close and reopen it.';return}
    snapshot();assignRecipeTweaking(meal,true,field.value);persist();close();refreshNeedsTweakingViews(updated);
   };actions.append(button)}
  }else{
   if(typeof meal.needsTweakingNote==='string'&&meal.needsTweakingNote.trim()){const note=document.createElement('p');note.className='recipe-tweaking-note';note.textContent=meal.needsTweakingNote;panel.append(note)}
   panel.append(recipeTweakingEditAction(()=>draw(true)));actions.style.cssText='display:flex;justify-content:flex-end';const dismiss=document.createElement('button');dismiss.type='button';setIconButton(dismiss,'cancel','Close Needs Adjusting');dismiss.onclick=close;actions.append(dismiss);
  }
  panel.append(actions);actions.lastElementChild.focus({preventScroll:true});
 }
 shade.append(panel);shade.addEventListener('click',e=>{if(e.target===shade)close()});
 shade.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();close()}if(e.key==='Tab'){const controls=[...panel.querySelectorAll('textarea,button')],first=controls[0],last=controls.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}});
 document.body.append(shade);draw(editing||meal.needsTweaking!==true);
}
function renderRecipeViewer(){
 const v=recipeViewer;if(!v)return;const meal=meals.find(m=>String(m.id)===v.mealId);if(!meal){if(v.activeTab!==v.anchorTab){closeLinkedRecipeTab(v.activeTab);return}closeRecipeViewer();return}
 updateCookingTimerSoundControls();renderRecipeTabs(v);v.cover.setAttribute('aria-label','Recipe: '+(meal.name||'Untitled meal'));
 cancelRecipeAdvance(v);clearRecipeLinkGestures(v);v.guidedCleanup?.();v.syncCleanup?.();v.autoComplete.disabled=false;v.autoComplete.checked=recipeViewPrefs.autoCompleteIngredients===true;v.keepScreenAwake.checked=recipeViewPrefs.keepScreenAwake!==false;
 const session=v.context?cookingSession(v.context):v.previewProgress,items=cookingItemTokens(meal),scroll=v.restoreTabScroll?v.activeTab.coverScroll:v.cover.scrollTop;const active=v.restoreTabScroll?v.activeTab.focusToken:document.activeElement?.dataset.cookingToken,scaleFocused=document.activeElement?.getAttribute('aria-label')==='Scale Recipe';const paneScroll=v.restoreTabScroll?v.activeTab.paneScroll:[...v.content.querySelectorAll('.recipe-pane')].map(p=>p.scrollTop);v.scaleCleanup?.();v.content.replaceChildren();v.cover.classList.toggle('recipe-split',recipeViewingMode()==='split');v.cover.classList.toggle('recipe-link-editing',!!v.linkEdit);setRecipeToolbarIcon(v.mode,recipeViewingMode()==='split'?'full':'split',recipeViewingMode()==='split'?'Full View':'Split View');v.mode.setAttribute('aria-pressed',String(recipeViewingMode()==='split'));

 const multiplier=v.context?occurrenceMultiplier(v.context):v.previewScale||1;const {scale}=buildRecipeTitleHeader(v,meal,multiplier);updateRecipeTimerReopenControl();renderRecipeTweakingStatus(v,meal);
 if(!v.context&&v.activeTab!==v.anchorTab){const notice=document.createElement('p');notice.className='recipe-occurrence-notice';notice.textContent='No definite scheduled occurrence for this link. Cooking progress and scaling stay in this viewer session.';v.content.append(notice)}
 if(v.linkEdit)v.linkIngredientTokens=new Set(recipeAssociationItems(meal).ingredients.map(i=>i.token));
 const panes=document.createElement('div');panes.className='recipe-panes';v.content.append(panes);
 const ingredientsPane=document.createElement('section');ingredientsPane.className='recipe-pane recipe-ingredients-pane';ingredientsPane.setAttribute('aria-label','Ingredients');
 const divider=document.createElement('div');divider.className='recipe-divider';divider.tabIndex=0;divider.setAttribute('role','separator');divider.setAttribute('aria-label','Resize ingredient and instruction sections');divider.setAttribute('aria-orientation','horizontal');divider.setAttribute('aria-valuemin','0');divider.setAttribute('aria-valuemax','100');
 const instructionsPane=document.createElement('section');instructionsPane.className='recipe-pane recipe-instructions-pane';instructionsPane.setAttribute('aria-label','Steps');panes.append(ingredientsPane,divider,instructionsPane);
 let destination=ingredientsPane;
 const section=(name)=>{const h=document.createElement('h2');h.textContent=name;destination.append(h)};
 const tapItem=(item,kind)=>{
  const el=document.createElement('button');el.className='cooking-item';el.textContent=kind==='ingredients'?scaleRecipeIngredient(item.text,multiplier):item.text;
  {el.type='button';el.dataset.cookingToken=item.token;const marked=!!session?.[kind].includes(item.token);el.classList.toggle('cooking-complete',marked);el.setAttribute('aria-pressed',String(marked));el.onclick=()=>{if(v.linkEdit){if(kind==='steps')beginRecipeLinkEdit(v,item.token);return}toggleCookingItem(kind,item.token)}}
  if(kind==='steps'){el.classList.toggle('recipe-link-selected',v.linkEdit?.step===item.token);bindRecipeStepLongPress(v,el,item.token)}
  return el;
 };
 section('Ingredients');const ul=document.createElement('ul');ul.className='recipe-viewer-ingredients';
 for(const item of recipeViewerIngredientOrder(meal,items)){const li=document.createElement('li');li.append(v.linkEdit?buildRecipeLinkIngredient(v,item,meal,multiplier,session):tapItem(item,'ingredients'));ul.append(li)}
 if(ul.children.length)destination.append(ul);else{const p=document.createElement('p');p.className='muted';p.textContent='No ingredients saved yet.';destination.append(p)}
 destination=instructionsPane;section('Steps');if(v.linkNotice){const notice=document.createElement('p');notice.className='recipe-link-message';notice.textContent=v.linkNotice;destination.append(notice)}let ol=null,stepCount=0;
 for(const originalItem of items.steps){const item=cleanInstructionBlock(originalItem);if(item.type==='section'){const h=document.createElement('h3');h.textContent=item.text;destination.append(h);ol=null;continue}
  if(!ol){ol=document.createElement('ol');ol.className='recipe-viewer-steps';destination.append(ol)}
  const li=document.createElement('li');li.append(tapItem(item,'steps'));addRecipeCookingTimer(li,meal,item,stepCount+1);
  ol.append(li);stepCount++;
 }
 if(!stepCount){const p=document.createElement('p');p.className='muted recipe-import-status';p.setAttribute('role','status');p.textContent=v.importMessage||'Instructions have not been imported. You can add them in Edit meal or view the original recipe.';destination.append(p)}
 const linked=[...new Set((Array.isArray(meal.linkedMealIds)?meal.linkedMealIds:[]).map(String))].map(id=>meals.find(m=>String(m.id)===String(id))).filter(m=>m&&m.id!==meal.id);
 if(linked.length){section('Linked recipes');for(const child of linked){const link=document.createElement('button');link.type='button';link.className='recipe-linked-link';link.textContent=child.name;link.onclick=()=>openLinkedRecipeTab(child);destination.append(link)}}
 if(meal.recipeImportReferences?.length){const review=document.createElement('button');review.type='button';review.className='recipe-linked-link';review.textContent='Review related recipe references ('+meal.recipeImportReferences.length+')';review.onclick=()=>{if(v.linkEdit){recipeLinkMessage(v,'Save or cancel ingredient links before reviewing related recipes.');return}openRecipeImportReview([meal],false)};destination.append(review)}
 if(meal.notes){section('Notes');const p=document.createElement('div');p.className='recipe-viewer-notes';p.textContent=normalizeRecipeText(meal.notes);destination.append(p)}

 if(meal.needsTweaking!==true){const tweaking=recipeTweakingAction('Needs Adjusting',()=>openNeedsTweaking(meal));tweaking.classList.add('recipe-needs-tweaking');destination.append(tweaking)}
 const original=recipeDisplaySourceUrl(meal);if(original){const link=document.createElement('a');link.className='recipe-original';link.href=original;link.target='_blank';link.rel='noopener noreferrer';link.textContent='View Original Recipe';destination.append(link)}
 if(v.advanceSpace&&recipeViewingMode()==='split')recipeAdvanceSpacer(v,instructionsPane);
 if(v.linkIngredientTailSpace){const tail=document.createElement('div');tail.className='recipe-link-ingredient-tail';tail.setAttribute('aria-hidden','true');tail.style.height=v.linkIngredientTailSpace+'px';ingredientsPane.append(tail)}
 if(v.linkTailSpace){const tail=document.createElement('div');tail.className='recipe-link-scroll-tail';tail.setAttribute('aria-hidden','true');tail.style.height=v.linkTailSpace+'px';instructionsPane.append(tail)}
 configureRecipeSplit(v,divider,panes);[ingredientsPane,instructionsPane].forEach((p,i)=>p.scrollTop=paneScroll[i]||0);v.cover.scrollTop=scroll;if(active){const target=[...v.content.querySelectorAll('[data-cooking-token]')].find(e=>e.dataset.cookingToken===active);target?.focus({preventScroll:true})}else if(scaleFocused)scale.focus({preventScroll:true});
 renderRecipeLinkBar(v);restoreRecipeLinkViewport(v,ingredientsPane,instructionsPane,scroll,paneScroll);
 configureRecipeIngredientSync(v,meal,ingredientsPane,instructionsPane);configureGuidedCooking(v,ingredientsPane,instructionsPane);configureCurrentRecipeStep(v,meal,session);v.restoreTabScroll=false;
}

const cookingRecipeStates=new Map();
function reconcileAllCookingData(){
 for(const meal of meals){
  const next={id:meal.id,ingredients:meal.ingredients,instructions:meal.instructions,ingredientStepLinks:meal.ingredientStepLinks};const text=JSON.stringify(next),prior=cookingRecipeStates.get(String(meal.id));
  if(prior!==text){reconcileCookingItems(prior?JSON.parse(prior):next,next);cookingRecipeStates.set(String(meal.id),text)}
 }
 reconcileCookingSchedule();
}
function clearCycledCookingContexts(selected){
 const predicate=c=>selected.some(item=>{const parent=String(item.parentId??item.linkedTo??'');return c.planId===String(item.planId)&&c.day===item.day&&((c.mealId===String(item.meal.id)&&c.parentId===parent)||(!parent&&!item.exact&&c.parentId===String(item.meal.id)&&!rotationGroupScheduled(mealPlans.find(p=>String(p.id)===c.planId),c.day,c.cat)))});resetCookingContexts(predicate);clearOccurrenceScales(c=>predicate(c)&&selected.some(item=>c.planId===String(item.planId)&&c.day===item.day&&(c.cat===item.cat||c.scaleGroupId===groupIdentity(item.cat)||c.parentId===String(item.meal.id)&&!rotationGroupScheduled(mealPlans.find(p=>String(p.id)===c.planId),c.day,c.cat))));
}
function clearCookingForSlots(records){
 const selected=[];
 for(const item of records){
  const id=item.mealId??item.meal?.id;if(id!=null)selected.push({planId:item.planId,day:item.day,cat:item.cat,meal:{id},parentId:item.parentId??item.linkedTo??'',exact:true});
  const plan=mealPlans.find(p=>p.id===item.planId);if(!plan||!rotationGroupScheduled(plan,item.day,item.cat))continue;
  const now=getDisplayedWeekdayMealsForPlan(plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan).find(e=>e.day===item.day&&e.cat===item.cat);
  if(now)selected.push({...now,planId:item.planId,exact:true});
 }
 for(const plan of mealPlans){const entries=getDisplayedWeekdayMealsForPlan(plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan).map(item=>({...item,planId:plan.id}));for(const item of cycleAffectedEntries(entries,selected.filter(x=>x.planId===plan.id),plan))selected.push({...item,exact:true})}
 clearCycledCookingContexts(selected);
}
function clearCookingForCycleBack(previous){
 const changed=previous.cookingCycledContexts||previousRotationSlots(previous).filter(old=>{
  const plan=mealPlans.find(p=>p.id===old.planId);const now=plan&&getDisplayedWeekdayMealsForPlan(plan).find(e=>e.day===old.day&&e.cat===old.cat);
  return !now||String(now.meal.id)!==String(old.meal.id);
 });
 clearCookingForSlots(changed);
}

async function acquireRecipeWakeLock(){
 const view=recipeViewer;
 if(!view||recipeViewPrefs.keepScreenAwake===false||document.visibilityState!=='visible'||!navigator.wakeLock?.request||view.wake||view.wakePending)return;
 const generation=++view.wakeRequest;view.wakePending=true;view.wakeSuspended=false;
 try{
  const lock=await navigator.wakeLock.request('screen');
  if(recipeViewer!==view||recipeViewPrefs.keepScreenAwake===false||generation!==view.wakeRequest||document.visibilityState!=='visible'){await lock.release();return}
  view.wake=lock;
  lock.addEventListener('release',()=>{
   if(view.wake===lock)view.wake=null;
   if(recipeViewer===view&&!view.wakeSuspended&&document.visibilityState==='visible'&&(view.wakeRetries||0)<2){view.wakeRetries=(view.wakeRetries||0)+1;clearTimeout(view.wakeRetry);view.wakeRetry=setTimeout(acquireRecipeWakeLock,1000)}
  },{once:true});
 }catch(e){/* Unsupported, denied, or interrupted wake locks never block recipe reading. */}
 finally{view.wakePending=false;if(recipeViewer===view&&generation!==view.wakeRequest&&document.visibilityState==='visible')acquireRecipeWakeLock()}
}
function releaseRecipeWakeLock(view){
 if(!view)return;view.wakeSuspended=true;view.wakeRequest++;clearTimeout(view.wakeRetry);const lock=view.wake;view.wake=null;
 if(lock&&!lock.released)Promise.resolve(lock.release()).catch(()=>{});
}
document.addEventListener('visibilitychange',()=>{

 const view=recipeViewer;if(!view)return;
 if(document.visibilityState==='visible'){view.wakeRetries=0;acquireRecipeWakeLock()}else releaseRecipeWakeLock(view);
});

window.addEventListener('beforeunload',()=>{recipePageLeaving=true});
window.addEventListener('pagehide',()=>{recipePageLeaving=true;if(recipeViewer)releaseRecipeWakeLock(recipeViewer)});
window.addEventListener('pageshow',()=>{recipePageLeaving=false;requestRecipeImportResume();if(recipeViewer){recipeViewer.wakeRetries=0;acquireRecipeWakeLock()}});