function recipeNotesText(value){return (Array.isArray(value)?value:[value]).filter(x=>x!=null).map(x=>normalizeRecipeText(typeof x==='object'?(x.text||x.description||x.name||''):x)).filter(Boolean).join('\n\n')}
// Parse only explicit instruction fields; never infer cooking directions from ingredients or notes.
function importedInstructionBlocks(value,depth=0){
 if(depth>24||value==null)return [];
 if(Array.isArray(value))return value.flatMap(v=>importedInstructionBlocks(v,depth+1));
 if(typeof value==='string'){
  const text=value.trim();if(!text)return [];
  if(/^[\[{]/.test(text)){try{const parsed=JSON.parse(text);if(parsed&&typeof parsed==='object')return importedInstructionBlocks(parsed,depth+1)}catch(e){}}
  // A fully bold sentence is still a cooking step, not an empty sequence of headings.
  return instructionBlocks(text.replace(/^\s*\*\*(\d+)\*\*\s*(?=\S)/gm,'$1. ').replace(/^\s*\*\*(.+[.!?])\*\*\s*$/gm,'$1'));
 }
 if(typeof value!=='object')return [];
 const type=String(value['@type']||value.type||'').toLowerCase();
 if(value.item!=null)return importedInstructionBlocks(value.item,depth+1);
 if(value.text&&typeof value.text==='object')return importedInstructionBlocks(value.text,depth+1);
 const children=value.itemListElement??value.steps??value.sections??value.instructions;
 if(children!=null){const parsed=importedInstructionBlocks(children,depth+1),heading=value.name||value.title||(type.includes('section')?value.text:'');if(parsed.length||type.includes('section'))return [...(heading?[{type:'section',text:normalizeRecipeText(heading)}]:[]),...parsed];return importedInstructionBlocks(value.text??value.description??value.name??'',depth+1)}
 for(const key of ['@value','value','html','markdown'])if(typeof value[key]==='string'&&value[key].trim())return importedInstructionBlocks(value[key],depth+1);
 const keys=Object.keys(value);if(keys.length&&keys.every(k=>/^\d+$/.test(k)))return keys.sort((a,b)=>Number(a)-Number(b)).flatMap(k=>importedInstructionBlocks(value[k],depth+1));
 return instructionBlocks(value);
}
function recipeImportInstructionValue(record){
 const values=['recipeInstructions','instructions','directions','method','steps'].map(key=>record?.[key]).filter(value=>value!=null);
 return values.find(value=>cleanupRecipeInstructions(value).instructions.some(block=>block.type==='step'&&block.text.trim()))??values.find(value=>importedInstructionBlocks(value).length)??values[0]??[];
}
function recipeInstructionReferenceResolver(root){
 const nodes=new Map(),visited=new WeakSet();
 function collect(value,depth=0){if(!value||typeof value!=='object'||depth>30||visited.has(value))return;visited.add(value);if(typeof value['@id']==='string'&&(!nodes.has(value['@id'])||Object.keys(value).length>Object.keys(nodes.get(value['@id'])).length))nodes.set(value['@id'],value);Object.values(value).forEach(child=>collect(child,depth+1))}collect(root);
 function resolve(value,seen=new Set(),depth=0){
  if(depth>24||value==null)return null;if(Array.isArray(value))return value.map(item=>resolve(item,new Set(seen),depth+1)).filter(item=>item!=null);
  if(typeof value!=='object')return value;
  const id=value['@id'];if(id&&nodes.has(id)){if(seen.has(id))return null;seen.add(id);value={...nodes.get(id),...value}}
  const copy={...value};for(const key of ['item','itemListElement','steps','sections','instructions','text','description'])if(copy[key]&&typeof copy[key]==='object')copy[key]=resolve(copy[key],new Set(seen),depth+1);return copy;
 }return resolve;
}
function recipeInstructionContainerHtml(node){
 const copy=node.cloneNode(true);copy.querySelectorAll('script,style,nav,footer,[role="navigation"],.advertisement,.adsbygoogle,[data-ad-slot]').forEach(el=>el.remove());
 return copy.getAttribute('content')||copy.innerHTML;
}
function recipeCardRecords(doc){
 const scopes=[...doc.querySelectorAll('[itemscope][itemtype*="Recipe"],.h-recipe,.hrecipe,.wprm-recipe-container,.tasty-recipes,.recipe-card')];
 const nodes=scopes.filter(node=>!scopes.some(parent=>parent!==node&&parent.contains(node)));
 if(!nodes.length&&doc.querySelector('[itemprop~="recipeInstructions"],.wprm-recipe-instructions-container,.tasty-recipes-instructions,.recipe-instructions'))nodes.push(doc.body);
 return nodes.flatMap(node=>{
  const get=selector=>{const el=node.querySelector(selector);return el?.getAttribute('content')||el?.getAttribute('datetime')||el?.textContent?.trim()||''};
  const name=get('[itemprop~="name"],.wprm-recipe-name,.tasty-recipes-title,.p-name,.fn,h1')||(nodes.length===1?doc.querySelector('h1')?.textContent?.trim():'');if(!name)return [];
  const all=[...node.querySelectorAll('[itemprop~="recipeInstructions"],.wprm-recipe-instructions-container,.tasty-recipes-instructions,.recipe-instructions,.e-instructions,.instructions')];
  const instructionNodes=all.filter(el=>!all.some(parent=>parent!==el&&parent.contains(el)));
  const recipeInstructions=instructionNodes.map(recipeInstructionContainerHtml).join('\n');
  const ingredients=[...node.querySelectorAll('[itemprop~="recipeIngredient"],.p-ingredient,.ingredient,.wprm-recipe-ingredient,.tasty-recipes-ingredients li')].map(el=>el.getAttribute('content')||el.textContent.trim());
  return [{name,recipeInstructions,recipeIngredient:ingredients,recipeCategory:[...node.querySelectorAll('[itemprop~="recipeCategory"]')].map(el=>el.textContent.trim()),notes:get('[itemprop~="recipeNotes"],.wprm-recipe-notes,.tasty-recipes-notes,.notes'),prepTime:get('[itemprop~="prepTime"]'),cookTime:get('[itemprop~="cookTime"]'),totalTime:get('[itemprop~="totalTime"]'),url:node.querySelector('[itemprop~="url"]')?.getAttribute('href')||doc.querySelector('link[rel="canonical"]')?.getAttribute('href')||''}];
 });
}
function mergeRecipeCardInstructions(records,cards){
 const result=records.map(record=>({...record}));
 for(const card of cards){
  const matches=result.filter(record=>recipeReferenceTitle(record.name||record.title)===recipeReferenceTitle(card.name)||recipeReferenceUrl(record.url||record['@id'])&&recipeReferenceUrl(record.url||record['@id'])===recipeReferenceUrl(card.url));
  // Merge only corroborated recipe identities; related cards remain separate.
  const target=matches.length===1?matches[0]:null;
  if(target){
   if(!cleanupRecipeInstructions(recipeImportInstructionValue(target)).instructions.some(block=>block.type==='step'))target.recipeInstructions=card.recipeInstructions;
   if(!recipeImportIngredients(target).length&&recipeImportIngredients(card).length)target.recipeIngredient=card.recipeIngredient;
   for(const key of ['prepTime','cookTime','totalTime'])if(recipeImportMinutes(target[key])===''&&recipeImportMinutes(card[key])!=='')target[key]=card[key];
  }
  else if(!matches.length)result.push(card);
 }return result;
}
// Import-only cleanup. Viewing or restoring an existing recipe never invokes this.
function recipeReferenceTitle(value){return normalizeRecipeText(value).normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim()}
function recipeReferenceUrl(value){
 try{const u=new URL(String(value||''));if(!['http:','https:'].includes(u.protocol))return '';
  if(/^(?:www\.|android\.)?recipesage\.com$/i.test(u.hostname)){const uuid=u.href.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);if(uuid)return recipeSageShareUrl(uuid[0].toLowerCase())}
  u.hash='';for(const key of [...u.searchParams.keys()])if(/^(?:utm_.+|fbclid|gclid)$/i.test(key))u.searchParams.delete(key);u.searchParams.sort();return u.href;
 }catch(e){return ''}
}
function recipeImportReference(value){
 if(value==null)return null;
 let name='',url='',sourceId='';
 if(typeof value==='object'){name=String(value.name||value.title||'');url=recipeReferenceUrl(value.url||value.recipeUrl||value.sourceUrl||value['@id']);sourceId=String(value.sourceId||value.importSourceId||value.recipeSageId||value.identifier||value.recipeId||value.id||value.uuid||'').trim()}
 else{const text=String(value).trim(),link=text.match(/^\[([^\]]+)\]\((https?:\/\/[^\s]+)(?:\s+"[^"]*")?\)$/i);if(link){name=link[1];url=recipeReferenceUrl(link[2])}else if(recipeReferenceUrl(text))url=recipeReferenceUrl(text);else if(recipeSageUuidPattern.test(text)||/^\d+$/.test(text))sourceId=text;else name=text}
 if(!sourceId&&/^https:\/\/android\.recipesage\.com\/api\/share\/recipe\//i.test(url))sourceId=url.split('/').at(-1);
 if(recipeSageUuidPattern.test(sourceId)){sourceId=sourceId.toLowerCase();if(!url)url=recipeSageShareUrl(sourceId)}
 name=normalizeRecipeText(name).replace(/^[-*•]\s+/,'').trim();return name||url||sourceId?{name,url,sourceId}:null;
}
function mergeRecipeImportReferences(...lists){
 const result=[],seen=new Set();for(const value of lists.flat()){const ref=recipeImportReference(value);if(!ref)continue;const key=ref.url?'url:'+ref.url:ref.sourceId?'id:'+ref.sourceId:'title:'+recipeReferenceTitle(ref.name);if(seen.has(key))continue;seen.add(key);result.push(ref)}return result;
}
function recipeImportLinkedReferences(r){
 const raw=r.linkedRecipes??r.linkedMeals??r.linkedRecipeIds??r.linkedMealIds??r.relatedRecipes??r.relatedMeals??[];
 return mergeRecipeImportReferences(Array.isArray(raw)?raw:typeof raw==='string'?raw.split(/[,\n;|]+/):[raw],Array.isArray(r.recipeImportReferences)?r.recipeImportReferences:[]);
}
function cleanupRecipeInstructions(value,{conservative=false}={}){
 const removed=[],related=[],imageRefs=new Set();
 // Keep link destinations until related-recipe extraction has finished.
 const prepare=(v,depth=0)=>{
  if(depth>24||v==null)return v;
  if(Array.isArray(v))return v.map(x=>prepare(x,depth+1));
  if(typeof v==='object'){const copy={...v};for(const key of ['text','description','name','title','@value','value','html','markdown','itemListElement','steps','sections','instructions'])if(key in copy)copy[key]=prepare(copy[key],depth+1);return copy}
  if(typeof v!=='string')return v;
  if(/^[\[{]/.test(v.trim())){try{const parsed=JSON.parse(v);if(parsed&&typeof parsed==='object')return prepare(parsed,depth+1)}catch(e){}}
  for(const match of v.matchAll(/!\[[^\]]*\]\[([^\]]+)\]/g))imageRefs.add(match[1].toLowerCase());
  v=v.replace(/<(https?:\/\/[^>]+)>/g,'$1');
  if(!/<\/?[a-z][^>]*>/i.test(v))return v;
  const doc=new DOMParser().parseFromString(v,'text/html');
  doc.querySelectorAll(conservative?'nav,script,style':'nav,footer,form,script,style').forEach(el=>{removed.push({text:el.textContent||el.tagName,reason:'Website navigation or metadata'});el.remove()});
  doc.querySelectorAll('img').forEach(el=>el.replaceWith('!['+(el.getAttribute('alt')||'')+']('+(el.getAttribute('src')||'')+')'));
  doc.querySelectorAll('a[href]').forEach(el=>el.replaceWith('['+el.textContent+']('+el.getAttribute('href')+')'));
  doc.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach(el=>el.replaceWith('\n## '+el.textContent+'\n'));
  if(conservative)doc.querySelectorAll('footer,form').forEach(el=>el.append('\n'));
  return normalizeRecipeText(conservative?'<div>'+doc.body.innerHTML+'</div>':doc.body.innerHTML);
 };
 const blocks=importedInstructionBlocks(prepare(value));let inRelated=false,relatedLogo=false;const instructions=[];
 const cooking=/\b(?:allow|arrange|beat|blend|bring|brush|discard|divide|fold|garnish|grease|keep|leave|let|line|measure|overmix|prepare|pulse|return|rub|set|spread|sprinkle|start|strain|take|taste|toss|turn|use|wait|wash|wrap|add|bake|boil|braise|broil|chill|chop|combine|cook|cool|cover|cut|drain|fry|grill|heat|knead|marinate|mix|place|pour|preheat|reduce|refrigerate|remove|rest|roast|season|serve|simmer|slice|stir|transfer|whisk)\b/i;
 const imageUrl=text=>/^<?https?:\/\/[^\s<>]+\.(?:avif|gif|jpe?g|png|svg|webp)(?:[?#][^\s<>]*)?>?$/i.test(text);
 const metadata=text=>/^(?:(?:log|sign)\s*in|sign\s*up|create (?:an? |your )?(?:free )?account)(?:(?:\s+(?:or|and)\s+)(?:(?:log|sign)\s*in|sign\s*up|create (?:an? |your )?(?:free )?account))?(?:\s+(?:to (?:save|share|edit|view|rate|comment on) (?:this |the |your )?recipe|to RecipeSage|for free))?[.!]?$/i.test(text)||/^(?:(?:download|install|get|try) (?:the )?RecipeSage(?: app)?(?: for (?:Android|iOS))?[.!]?|forgot (?:your )?password\??|privacy policy|terms (?:of service|and conditions)|all rights reserved[.]?|powered by RecipeSage[.]?|RecipeSage|home\s*[|·]\s*recipes(?:\s*[|·]\s*(?:about|contact|log in|sign up))*)$/i.test(text)||/^(?:URL Source:\s*https?:\/\/\S+|Markdown Content:|(?:Recipe ID|Recipe UUID):\s*[0-9a-f-]{36}|Copyright\s+(?:©\s*)?\d{4}(?:[-–]\d{4})?\s+[^.!?]{1,100})$/i.test(text)||/^(?:(?:recipe\s+)?(?:created(?:\s+(?:on|at))?|date created|last[ -]*(?:edited|updated|modified)(?:\s+(?:on|at))?|updated(?:\s+(?:on|at))?|published(?:\s+(?:on|at))?|datePublished|dateModified|Published Time))\s*:?\s*(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[T ,][\d: .+ZUTC-]+)?|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}(?:\s+(?:at\s+)?[\d: APMapmTZ+-]+)?)\s*[.]?$/i.test(text);
 for(const block of blocks){
  let kept=[];
  const flush=()=>{if(kept.length){const next={...block,text:kept.join('\n')};instructions.push(next);kept=[]}};
  for(const line of String(block.text||'').split(/\r?\n/)){
   const plain=line.trim().replace(/^\s*(?:(?:step\s+)?\d+[.)]\s*|[-*•]\s+)/i,'').replace(/\*\*|__/g,'').trim();
   const heading=plain.replace(/^\d+\s+(?=(?:linked|related)\s+(?:recipes?|meals?))/i,'').replace(/\[([^\]]+)\]\([^)]*\)/g,'$1').replace(/^#{1,6}\s*/,'').replace(/:\s*$/,'').trim();
   const drop=reason=>removed.push({text:line,reason});
   if(!conservative&&(/^(?:linked|related)\s+(?:recipes?|meals?)$|^(?:see also|more recipes)$/i.test(heading))){flush();inRelated=true;drop('Related recipe section');continue}
   const uncertainImage=conservative&&(/\[!\[/.test(line)||[...line.matchAll(/!\[([^\]]*)\]/g)].some(m=>m[1].trim()&&!/^(?:image|photo|picture|thumbnail|img)(?:\s*\d+)?$|^recipe (?:image|photo)$/i.test(m[1].trim())));
   const withoutImages=uncertainImage?line.trim():line.replace(/\[(!\[[^\]]*\]\([^\n]*?\))\]\([^\n]*?\)/g,'$1').replace(/!\[[^\]]*\]\((?:<[^>]*>|[^)\n]*)\)|!\[[^\]]*\]\[[^\]]*\]/g,'').trim();
   const remainder=withoutImages.replace(/\*\*|__/g,'').replace(/^\s*(?:\d+(?:[.)]|\s*$)\s*|[-*•]\s+)/,'').trim();
   const definition=plain.match(/^\[([^\]]+)\]:\s*(\S+)(?:\s+.*)?$/);
   if((withoutImages!==line.trim()&&!remainder)||imageUrl(plain)||/^data:image\//i.test(plain)||(definition&&(imageRefs.has(definition[1].toLowerCase())||imageUrl(definition[2])))){if(inRelated&&/https:\/\/recipesage\.com\/app\/assets\/imgs\/logo_green_padded\.png/.test(line))relatedLogo=true;drop('Image reference');continue}
   const content=withoutImages.replace(/^\s*(?:(?:step\s+)?\d+[.)]\s*|[-*•]\s+)/i,'').replace(/\*\*|__/g,'').trim();
   const metadataText=content.replace(/\[([^\]]+)\]\([^)]*\)/g,'$1');
   if(metadata(metadataText)||recipeRepairBoilerplate(recipeRepairLegacyLine(metadataText).text,recipeRepairLegacyLine(content).links)){drop('Website metadata or account prompt');continue}
   if(inRelated){
    const ref=recipeImportReference(content),pureLink=/^(?:\[[^\]]+\]\(https?:\/\/[^\s]+\)|https?:\/\/\S+)$/i.test(content);
    if(/^(?:instructions|directions|method|preparation|cooking instructions)$/i.test(heading))inRelated=false;
    const titleOnly=inRelated&&block.type!=='section'&&content.length<=100&&/^[\p{L}][\p{L}\p{N} &'’(),/-]*$/u.test(content)&&!cooking.test(content)&&(!/[0-9]/.test(content))&&content.split(/\s+/).every(word=>/^[A-Z\p{Lu}]/u.test(word)||/^(?:a|an|and|the|with|of|for|in|or|to)$/i.test(word))&&! /\b(?:minutes?|hours?|degrees?|cups?|tbsp|tsp)\b/i.test(content);
    if(inRelated&&ref&&relatedLogo&&block.type==='section'&&content.length<=100&&content.split(/\s+/).length>1&&!cooking.test(content)){related.push(ref);drop('RecipeSage related recipe heading');relatedLogo=false;continue}
    if(inRelated&&ref&&(pureLink||titleOnly)){related.push(ref);drop('Related recipe reference');continue}
    // Any new section or uncertain prose ends the reference list, rather than eating a cooking step.
    inRelated=false;
   }
   if(!withoutImages)continue;
   if(withoutImages!==line.trim())removed.push({text:line,reason:'Inline image removed; cooking text retained'});
   kept.push(withoutImages);
  }
  flush();
 }
 return {instructions,related:mergeRecipeImportReferences(related),removed};
}
function findRelatedImportedMeal(ref,library=meals,parent=null){
 ref=recipeImportReference(ref);if(!ref)return null;
 const candidates=library.filter(m=>m!==parent&&String(m.id)!==String(parent?.id)&&!(parent?.linkGroup&&m.linkGroup===parent.linkGroup));
 const urls=m=>[m.url,m.originalRecipeUrl,m.ingredientImportUrl,m.sourceUrl].map(recipeReferenceUrl).filter(Boolean);
 let found=ref.sourceId?candidates.filter(m=>[m.importSourceId,m.recipeSageId].some(v=>String(v||'')===ref.sourceId)):[];
 if(!found.length&&ref.url)found=candidates.filter(m=>urls(m).includes(ref.url));
 if(!found.length&&ref.name)found=candidates.filter(m=>recipeReferenceTitle(m.name)===recipeReferenceTitle(ref.name)&&((!ref.sourceId&&!ref.url)||(!m.importSourceId&&!m.recipeSageId&&!urls(m).length)));
 if(found.length>1){const saved=found.filter(m=>(parent?.linkedMealIds||[]).some(id=>String(id)===String(m.id)));if(saved.length===1)return saved[0];if(found.every(m=>m.linkGroup&&m.linkGroup===found[0].linkGroup))return found[0];return null}
 return found[0]||null;
}

// References are import metadata only. Confirmed relationships use linkedMealIds.
function openRecipeImportReview(targets,previewCleanup=true){
 const rows=targets.map(m=>meals.find(x=>String(x.id)===String(m.id))).filter(Boolean).map(meal=>{
  const cleanup=cleanupRecipeInstructions(meal.instructions),references=mergeRecipeImportReferences(meal.recipeImportReferences||[],cleanup.related);
  return {meal,cleanup,references,checks:[]};
 });if(!rows.length)return;
 const originalData=JSON.stringify({cats,active,meals}),controller=new AbortController(),focus=document.activeElement;
 const overlay=document.createElement('div');overlay.id='recipeImportReview';overlay.className='recipe-import-review';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-labelledby','recipeImportReviewTitle');
 const panel=document.createElement('section'),title=document.createElement('h2');title.id='recipeImportReviewTitle';title.textContent=previewCleanup?'Review instruction cleanup':'Review related recipes';panel.append(title);
 const help=document.createElement('p');help.textContent='Only clearly identified clutter is removed. Review the preview before saving. Related recipes are optional; only checked links will be added. Linked meals follow this recipe when it is scheduled.';panel.append(help);
 const content=document.createElement('div');content.className='recipe-import-review-content';panel.append(content);
 for(const row of rows){
  const section=document.createElement('section'),heading=document.createElement('h3');heading.textContent=row.meal.name;section.append(heading);
  if(previewCleanup){
   const info=document.createElement('p');info.textContent=row.cleanup.removed.length?row.cleanup.removed.length+' identified clutter entries or fragments removed. You can edit the proposed instructions.':'No clearly identifiable instruction clutter found. Uncertain content is preserved.';section.append(info);
   const before=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Original instructions';const text=document.createElement('pre');text.textContent=instructionEditorText(row.meal.instructions);before.append(summary,text);section.append(before);
   const label=document.createElement('label');label.textContent='Proposed instructions';const area=document.createElement('textarea');area.className='ingredients-input';area.value=instructionEditorText(row.cleanup.instructions);area.setAttribute('aria-label','Proposed instructions for '+row.meal.name);label.append(area);section.append(label);row.area=area;
   if(row.cleanup.removed.length){const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Removed content';const list=document.createElement('pre');list.textContent=row.cleanup.removed.map(item=>item.reason+': '+item.text).join('\n\n');details.append(summary,list);section.append(details)}
  }
  const linksHeading=document.createElement('h4');linksHeading.textContent='Related recipes';section.append(linksHeading);
  if(!row.references.length){const none=document.createElement('p');none.textContent='No related recipe references found.';section.append(none)}
  const shownTargets=new Set();
  for(const ref of row.references){
   const match=findRelatedImportedMeal(ref,meals,row.meal),label=document.createElement('label');label.className='recipe-import-reference';
   if(match&&shownTargets.has(String(match.id)))continue;if(match)shownTargets.add(String(match.id));
   const self=!!findRelatedImportedMeal(ref,[row.meal]);
   const cb=document.createElement('input');cb.type='checkbox';cb.checked=!!match&&(row.meal.linkedMealIds||[]).some(id=>String(id)===String(match.id));
   const ambiguous=!match&&!ref.url&&!ref.sourceId&&meals.some(m=>m!==row.meal&&recipeReferenceTitle(m.name)===recipeReferenceTitle(ref.name));
   cb.disabled=self||(!match&&(!ref.url||ambiguous));
   const text=document.createElement('span'),name=ref.name||match?.name||ref.url||ref.sourceId;
   text.textContent=name+' — '+(self?'This is the current recipe':match?'Use existing meal':ambiguous?'Existing title needs review in Linked Meals':ref.url?'Import and link':'No usable source; choose manually in Linked Meals');
   cb.setAttribute('aria-label','Link '+name);label.append(cb,text);section.append(label);row.checks.push({ref,match,cb});
  }
  content.append(section);
 }
 const status=document.createElement('p');status.setAttribute('role','status');panel.append(status);
 const relatedRotation=document.createElement('input');relatedRotation.type='checkbox';relatedRotation.checked=true;stage2FormField(panel,'Add newly imported related recipes to rotation',relatedRotation);
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Save reviewed recipe changes');setIconButton(cancel,'cancel','Cancel recipe review');actions.append(save,cancel);panel.append(actions);overlay.append(panel);
 const inert=[...document.body.children].map(el=>[el,el.inert]);inert.forEach(([el])=>el.inert=true);document.body.append(overlay);
 const close=()=>{controller.abort();overlay.remove();for(const [el,was] of inert)if(el.isConnected)el.inert=was;focus?.isConnected&&focus.focus({preventScroll:true})};cancel.onclick=close;
 overlay.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();close()}if(e.key==='Tab'){const items=[...overlay.querySelectorAll('button:not([disabled]),input:not([disabled]),textarea,summary')].filter(e=>e.getClientRects().length),first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}});
 save.onclick=async()=>{
  save.disabled=true;const next=meals.map(m=>({...m}));let nextId=id;
  try{
   if(originalData!==JSON.stringify({cats,active,meals}))throw Error('The recipes changed while this review was open. Cancel and reopen the review.');
   for(const row of rows){
    const target=next.find(m=>String(m.id)===String(row.meal.id));
    if(row.area&&row.area.value!==instructionEditorText(row.meal.instructions))target.instructions=instructionBlocks(row.area.value);
    target.recipeImportReferences=row.references;
    let linked=[...(target.linkedMealIds||[])];
    for(const choice of row.checks){
     if(choice.cb.disabled)continue;
     let match=findRelatedImportedMeal(choice.ref,next,target);
     if(!choice.cb.checked){if(match)linked=linked.filter(id=>String(id)!==String(match.id));continue}
     if(!match){
      status.textContent='Importing '+(choice.ref.name||choice.ref.url)+'…';
      const lines=await importIngredientsFromWebsite(choice.ref.url,controller.signal,choice.ref.name),details=lines.recipeDetails;
      if(controller.signal.aborted||!overlay.isConnected)return;
      if(!details||(!details.ingredients?.length&&!details.instructions?.some(b=>b.type==='step'))||!(details.name||choice.ref.name))throw Error('This source did not provide a usable recipe. No changes were saved.');
      if(details.name&&choice.ref.name&&recipeReferenceTitle(details.name)!==recipeReferenceTitle(choice.ref.name))throw Error('The source returned a different recipe title. Import it separately for review. No changes were saved.');
      if(findRelatedImportedMeal({url:details.originalRecipeUrl},[target]))throw Error('The source points to the current recipe, so no self-link was added. No changes were saved.');
      // Check identifiers again against staged imports, so multiple parents reuse one recipe.
      match=findRelatedImportedMeal({name:details.name,url:choice.ref.url,sourceId:choice.ref.sourceId},next,target)||findRelatedImportedMeal({url:details.originalRecipeUrl},next,target);
      if(!match){match={...details,id:nextId++,cat:target.cat,name:details.name||choice.ref.name,url:choice.ref.url,importSourceId:choice.ref.sourceId||undefined,recipeSageId:recipeSageUuidPattern.test(choice.ref.sourceId)?choice.ref.sourceId:'',rotation:relatedRotation.checked,groceryDefaultAll:true,keepAsIdea:!relatedRotation.checked,labels:[],recipeImportPending:false};next.push(match)}
     }
     linked.push(match.id);
    }
    target.linkedMealIds=[...new Set(linked)].filter(id=>String(id)!==String(target.id));
    if(target.instructions!==row.meal.instructions&&Array.isArray(target.ingredientStepLinks))target.ingredientStepLinks=validRecipeIngredientLinks(target);
    assignSharedRecipeFields(target,sharedRecipeChanges(row.meal,target),next);
   }
   if(controller.signal.aborted||!overlay.isConnected)return;
   if(originalData!==JSON.stringify({cats,active,meals}))throw Error('The recipes changed while sources were loading. Cancel and reopen the review.');
   try{localStorage.setItem('mealRotationDataV1',JSON.stringify({cats,active,meals:next}))}catch(e){throw Error('Changes could not be saved. Your previous recipes are unchanged; free some browser storage and try again.')}
   snapshot();meals=next;id=nextId;close();reconcileAllCookingData();
   if(recipeViewer){recipeViewer.contentChanged=true;renderRecipeViewer()}else render();
  }catch(e){if(!controller.signal.aborted&&overlay.isConnected){status.textContent=e.message||'The recipe could not be imported. No changes were saved.';save.disabled=false}}
 };
 cancel.focus({preventScroll:true});
}

function cleanImportedRecipeNotes(value,source=''){
 const notes=recipeNotesText(value),legacy=recipeRepairLegacyNotes({notes,url:source},[]);if(legacy.notes===null)return {notes,related:[]};
 const marker=notes.search(/^(?:#{1,6}\s*)?(?:linked|related) recipes\s*:?\s*$/im);
 if(marker>=0&&/https:\/\/recipesage\.com\/app\/assets\/imgs\/logo_green_padded\.png/.test(notes.slice(marker))){const tail=cleanupRecipeInstructions(notes.slice(marker));return {notes:(notes.slice(0,marker)+instructionEditorText(tail.instructions)).trim(),related:tail.related}}
 return {notes:legacy.notes,related:[]};
}
function recipeInstructionAudit(meal){
 const blocks=importedInstructionBlocks(meal.instructions),steps=blocks.filter(block=>block.type==='step'&&block.text.trim());
 const suspicious=blocks.some(block=>String(block.text).split(/\r?\n/).some(line=>{const parsed=recipeRepairLegacyLine(line);return !!recipeRepairBoilerplate(parsed.text,parsed.links)||/^(?:linked|related) recipes\s*:?$/i.test(parsed.text)}));
 return {missing:recipeRepairEmpty(meal.instructions),headingOnly:!steps.length&&!recipeRepairEmpty(meal.instructions),suspicious};
}
function recipeUrlRepairPlan(items,library=meals,urlRepairs=new Map(),allowWeb=false){
 const plan=recipeRepairPlan(items,library,allowWeb);
 for(const row of plan.rows){
  const result=urlRepairs.get(String(row.meal.id)),audit=recipeInstructionAudit(row.meal);
  if(audit.headingOnly)row.uncertain.push('No cooking steps found, but saved headings/other text were preserved. Review in Edit meal.');
  if(audit.suspicious&&row.instructions===null&&!row.removedSaved.length)row.uncertain.push('Possible website text retained for manual review; safe removal could not be verified.');
  if(!result)continue;
  if(result.error){row.reason+=' Source retry: '+result.error+' Saved content preserved; manual correction is available in Edit meal.';continue}
  const empty=recipeRepairEmpty(row.cleanup.instructions??row.meal.instructions);
  if(!empty){row.reason+=' Existing instructions preserved; source instructions not substituted.';continue}
  if(row.meal.ingredientStepLinks!=null&&(!Array.isArray(row.meal.ingredientStepLinks)||row.meal.ingredientStepLinks.length)||Object.values(cookingSessions.occurrences).some(session=>session.context.mealId===String(row.meal.id)&&session.steps.length)){row.reason+=' Saved step associations/progress require manual review; source instructions not applied.';continue}
  if(!result.instructions?.some(block=>block.type==='step')){row.reason+=' Source provided no reliable instructions; saved content preserved.';continue}
  row.instructions=JSON.parse(JSON.stringify(result.instructions));row.kind=row.kind.includes('cleanup')?'restore+cleanup':'restore';row.reason='Preview missing instructions retrieved from the saved recipe URL.';row.method='Saved source: '+result.url+'; only instructions will change. Existing titles, ingredients, notes, links and cooking data are retained.';row.match=true;
 }
 plan.ready=plan.rows.filter(row=>row.instructions!==null||row.notes!==null);plan.restoring=plan.ready.filter(row=>row.kind.includes('restore')).length;plan.cleaning=plan.ready.filter(row=>row.kind.includes('cleanup')).length;plan.matched=plan.rows.filter(row=>row.match).length;plan.uncertain=plan.rows.filter(row=>row.uncertain.length||row.cleanup.reason).length;return plan;
}
function completeRecipeFields(r,source=''){
 const props=Array.isArray(r.additionalProperty)?r.additionalProperty:[];
 const rawMarinate=r.marinateTime??r.marinatingTime??r.marinate_time??r.marinate??props.find(p=>/marinat/i.test(p.name||''))?.value??'';
 const marinate=typeof rawMarinate==='string'&&/[-–]/.test(rawMarinate)?rawMarinate:(recipeImportMinutes(rawMarinate)!==''?recipeImportMinutes(rawMarinate):String(rawMarinate||''));
 const original=r.originalRecipeUrl||r.sourceUrl||r.source_url||(typeof r.isBasedOn==='object'?r.isBasedOn?.url:r.isBasedOn)||(typeof r.url==='object'?r.url?.url:r.url)||source;
 let originalRecipeUrl='';try{if(original){const u=new URL(original,source||undefined);if(['http:','https:'].includes(u.protocol))originalRecipeUrl=u.href}}catch(e){}
 const cleanup=cleanupRecipeInstructions(recipeImportInstructionValue(r)),noteParts=cleanImportedRecipeNotes(r.recipeNotes??r.notes??r.note??r.description??'',typeof r.url==='string'?r.url:source||originalRecipeUrl);
 return {recipeImportReferences:mergeRecipeImportReferences(recipeImportLinkedReferences(r),cleanup.related,noteParts.related),name:normalizeRecipeText(r.name||r.title||''),ingredients:recipeImportIngredients(r).map(ingredientLine).filter(Boolean),instructions:cleanup.instructions.map(cleanInstructionBlock),notes:noteParts.notes,prep:recipeImportMinutes(r.prepTime??r.prep_time??r.activeTime??r.prep),cook:recipeImportMinutes(r.cookTime??r.cook_time??r.cook),total:recipeImportMinutes(r.totalTime??r.total_time??r.total),marinate,originalRecipeUrl};
}
function recipeTextSections(text){
 const lines=String(text||'').split(/\r?\n/);let mode='',instructions=[],notes=[];
 for(const line of lines){const heading=line.trim().replace(/^#{1,6}\s*/, '').replace(/\*\*/g,'').replace(/:$/,'');
  if(/^(?:instructions|directions|method|preparation|cooking instructions)$/i.test(heading)){mode='instructions';continue}
  if(/^(?:notes|recipe notes|tips)$/i.test(heading)){mode='notes';continue}
  if(/^(?:nutrition|nutrition facts|comments|reviews|equipment|ingredients)$/i.test(heading)){mode='';continue}
  if(/^\s*[-=]{3,}\s*$/.test(line))continue;
  if(mode==='instructions')instructions.push(line);else if(mode==='notes')notes.push(line);
 }
 if(!instructions.length&&/URL Source:\s*https?:\/\/(?:android\.)?recipesage\.com\//i.test(String(text))&&/Markdown Content:/i.test(String(text))){
  const body=String(text).split(/Markdown Content:\s*\n/i).slice(1).join('\n').trim();
  const numbered=[...body.matchAll(/^\s*(?:\*\*(\d+)\*\*|(\d+)[.)])\s*(\S.*)$/gm)];
  const cooking=/\b(?:brown|add|cook|heat|preheat|mix|stir|pour|bake|remove|put|place|serve|simmer|roast|marinate|refrigerate|whisk|chop|bring|rest|drain)\b/i;
  if(numbered.length>=2&&Number(numbered[0][1]||numbered[0][2])===1&&numbered.every((match,index)=>Number(match[1]||match[2])===index+1)&&numbered.filter(match=>cooking.test(match[3])&&match[3].split(/\s+/).length>=6).length>=2&&/^\s*(?:\*\*1\*\*|1[.)])/.test(body))instructions.push(body);
 }
 const cleanup=cleanupRecipeInstructions(instructions.join('\n'));const name=(String(text).match(/^Title:\s*(.+)$/m)||[])[1]||'';
 const noteText=notes.join('\n').trim(),source=(String(text).match(/^URL Source:\s*(https?:\/\/\S+)/m)||[])[1]||'';
 const cleanedNotes=cleanImportedRecipeNotes(noteText,source);
 return {name,instructions:cleanup.instructions.map(cleanInstructionBlock),recipeImportReferences:mergeRecipeImportReferences(cleanup.related,cleanedNotes.related),notes:cleanedNotes.notes};
}
function extractCompleteRecipe(payload,source='',expectedName=''){
 const raw=String(payload||'').trim();let candidates=[];
 function collect(value,depth=0,resolve=recipeInstructionReferenceResolver(value)){
  if(!value||typeof value!=='object'||depth>16)return;if(Array.isArray(value)){value.forEach(item=>collect(item,depth+1,resolve));return}
  const type=String(value['@type']||'');
  if((/recipe/i.test(type)||((value.name||value.title)&&(value.recipeIngredient||value.ingredients||value.instructions||value.recipeInstructions||value.directions)))&&!/ItemList/i.test(type))candidates.push({...value,recipeInstructions:resolve(recipeImportInstructionValue(value))});
  for(const key of ['@graph','@included','recipes','recipe','data','items','mainEntity','mainEntityOfPage','itemListElement','item','result'])if(value[key]&&typeof value[key]==='object')collect(value[key],depth+1,resolve);
  for(const key of ['contents','content'])if(typeof value[key]==='string'&&value[key].trim()){const nested=extractCompleteRecipe(value[key],source,expectedName);if(nested)candidates.push({name:nested.name,recipeIngredient:nested.ingredients,recipeInstructions:nested.instructions,notes:nested.notes,prepTime:nested.prep,cookTime:nested.cook,totalTime:nested.total,marinate:nested.marinate,originalRecipeUrl:nested.originalRecipeUrl,recipeImportReferences:nested.recipeImportReferences})}
 }
 if(raw[0]==='{'||raw[0]==='['){try{collect(JSON.parse(raw))}catch(e){}}
 if(/<\w|<!doctype/i.test(raw)){
  const doc=new DOMParser().parseFromString(raw,'text/html');doc.querySelectorAll('script[type="application/ld+json"]').forEach(node=>{try{collect(JSON.parse(node.textContent))}catch(e){}});
  candidates=mergeRecipeCardInstructions(candidates,recipeCardRecords(doc));
 }
 const exact=candidates.filter(record=>expectedName&&recipeReferenceTitle(record.name||record.title)===recipeReferenceTitle(expectedName));
 const byUrl=candidates.filter(record=>[record.url,record['@id'],record.mainEntityOfPage?.['@id'],record.mainEntityOfPage,record.originalRecipeUrl].some(value=>typeof value==='string'&&recipeReferenceUrl(value)===recipeReferenceUrl(source)));
 const pool=byUrl.length?byUrl:exact.length?exact:candidates;
 const usable=pool.filter(record=>cleanupRecipeInstructions(recipeImportInstructionValue(record)).instructions.some(block=>block.type==='step'));
 const best=usable.length===1?usable[0]:pool[0];
 if(best){const fields=completeRecipeFields(best,source);if(!exact.length&&!byUrl.length&&usable.length>1){fields.instructions=[];fields.instructionWarning='Several recipes were found; instructions need manual review.'}if(fields.ingredients.length||fields.instructions.some(block=>block.type==='step'))return fields}
 const readerSource=(raw.match(/^URL Source:\s*(https?:\/\/\S+)/m)||[])[1];if(readerSource&&source&&recipeReferenceUrl(readerSource)!==recipeReferenceUrl(source))return null;
 const parts=recipeTextSections(raw),ingredients=extractRecipeIngredients(raw);
 if(parts.instructions.some(block=>block.type==='step')||ingredients.length)return {...parts,name:parts.name||'',ingredients,prep:'',cook:'',total:'',marinate:'',originalRecipeUrl:source};
 return null;
}
function fillMissingRecipeContent(target,details){
 if(!details)return false;let changed=false;
 const refs=mergeRecipeImportReferences(target.recipeImportReferences||[],details.recipeImportReferences||[]);if(refs.length&&JSON.stringify(refs)!==JSON.stringify(target.recipeImportReferences||[])){target.recipeImportReferences=refs;changed=true}
 if((!target.name||target.name==='Untitled meal')&&details.name){target.name=details.name;changed=true}
 const set=(key,value)=>{if(value!==''&&value!=null&&(!(key in target)||target[key]===''||target[key]==null)){target[key]=value;changed=true}};
 if(recipeRepairEmpty(target.instructions)&&(!target.ingredientStepLinks||Array.isArray(target.ingredientStepLinks)&&!target.ingredientStepLinks.length)&&!Object.values(cookingSessions.occurrences).some(session=>session.context.mealId===String(target.id)&&session.steps.length)&&details.instructions?.some(b=>b.type==='step')){target.instructions=JSON.parse(JSON.stringify(details.instructions));changed=true}
 if(!target.notes&&details.notes){target.notes=details.notes;changed=true}
 if((!Array.isArray(target.ingredients)||!target.ingredients.length)&&details.ingredients?.length){target.ingredients=[...details.ingredients];changed=true}
 for(const key of ['prep','cook','total','marinate','originalRecipeUrl'])set(key,details[key]);return changed;
}
function recipeImportTargetSignature(meal){return JSON.stringify([String(meal.id),String(meal.importSourceId||''),String(meal.url||''),String(meal.ingredientImportUrl||''),String(meal.sourceUrl||'')])}
function saveEnrichedRecipe(mealId,details){
 const meal=meals.find(m=>String(m.id)===String(mealId));if(!meal||backupRestoreReloadPending||recipePageLeaving||(details?.importTargetSignature&&details.importTargetSignature!==recipeImportTargetSignature(meal)))return false;
 const affected=meals.filter(m=>m===meal||(meal.linkGroup&&m.linkGroup===meal.linkGroup));if(recipeBackgroundWritesBlocked())return false;
 const replacements=new Map();for(const m of affected){const copy={...m};if(fillMissingRecipeContent(copy,details))replacements.set(m,copy)}
 if(!replacements.size)return false;
 const next=meals.map(m=>replacements.get(m)||m);
 try{localStorage.setItem('mealRotationDataV1',JSON.stringify({cats,active,meals:next}))}catch(e){return false}
 for(const [m,copy] of replacements)Object.assign(m,copy);if(recipeViewer)recipeViewer.contentChanged=true;reconcileAllCookingData();return true;
}
const recipeImportFailures=new Map();
async function fetchInternalRecipe(meal,signal){
 const url=String(recipeOriginalUrl(meal)||meal.url||'');if(!url)throw Error('No recipe URL is saved.');
 if(Date.now()-(recipeImportFailures.get(url)||0)<30000)throw Error('The source could not be read recently. Try again later.');
 const targetSignature=recipeImportTargetSignature(meal);
 try{const lines=await importIngredientsFromWebsite(url,signal,meal.name);const details=lines.recipeDetails||{ingredients:lines,instructions:[],notes:'',originalRecipeUrl:recipeOriginalUrl(meal)};details.importTargetSignature=targetSignature;return details}
 catch(e){if(!signal?.aborted)recipeImportFailures.set(url,Date.now());throw e}
}
async function enrichViewedRecipe(meal){
 if(instructionBlocks(meal.instructions).some(x=>x.type==='step')||!recipeOriginalUrl(meal))return;
 const view=recipeViewer;if(!meal.recipeImportPending){view.importMessage='Instructions are missing. Add them in Edit recipe, or import a complete recipe file from Settings → Recipes.';renderRecipeViewer();return}const tab=view.activeTab,controller=new AbortController();view.importController=controller;view.importMessage='Importing recipe details…';renderRecipeViewer();
 try{const details=await fetchInternalRecipe(meal,controller.signal);if(recipeViewer!==view||view.activeTab!==tab||controller.signal.aborted)return;
  const changed=saveEnrichedRecipe(meal.id,details);view.importMessage=instructionBlocks(meal.instructions).some(x=>x.type==='step')?'':(changed?'Available recipe details were imported, but this source did not provide instructions. Add instructions in Edit meal or view the original recipe.':'Instructions could not be saved or were unavailable. Existing recipe content has been kept.');renderRecipeViewer();
 }catch(e){if(recipeViewer!==view||view.activeTab!==tab||controller.signal.aborted)return;view.importMessage='Instructions could not be imported from this source. Your saved ingredients and details are still available; add instructions in Edit meal or view the original recipe.';renderRecipeViewer()}
}
function recipeBackgroundWritesBlocked(){return editId!==null||!!document.querySelector('[data-recipe-edit-draft], [role="dialog"]:not(#recipeViewer)')}
const recipeImportJobs=new Set(),recipeImportInFlight=new Set();let recipeImportWorkersActive=false,recipeImportResumeTimer=null,recipePageLeaving=false;
function recordRecipeImportAttempt(id,pending,retryAt=0,signature=null){
 const meal=meals.find(m=>m.id===id);if(!meal||backupRestoreReloadPending||recipePageLeaving||recipeBackgroundWritesBlocked()||(signature&&recipeImportTargetSignature(meal)!==signature))return;
 const replacement={...meal,recipeImportPending:pending,recipeImportRetryAt:retryAt};
 try{localStorage.setItem('mealRotationDataV1',JSON.stringify({cats,active,meals:meals.map(m=>m===meal?replacement:m)}));Object.assign(meal,replacement)}catch(e){/* Keep the previously saved record and pending job. */}
}
async function enrichImportedRecipes(ids){
 for(const id of ids)if(!recipeImportInFlight.has(id))recipeImportJobs.add(id);if(recipeImportWorkersActive||recipePageLeaving||recipeBackgroundWritesBlocked())return;recipeImportWorkersActive=true;
 async function worker(){while(recipeImportJobs.size){if(recipePageLeaving||recipeBackgroundWritesBlocked())break;const id=recipeImportJobs.values().next().value;recipeImportJobs.delete(id);const meal=meals.find(m=>m.id===id);
  if(!meal||instructionBlocks(meal.instructions).some(b=>b.type==='step')||!recipeOriginalUrl(meal))continue;const signature=recipeImportTargetSignature(meal);recipeImportInFlight.add(id);
  try{const details=await fetchInternalRecipe(meal);saveEnrichedRecipe(id,details);const needsSave=details.instructions?.some(b=>b.type==='step')&&!instructionBlocks(meals.find(m=>m.id===id)?.instructions).some(b=>b.type==='step');recordRecipeImportAttempt(id,!!needsSave,needsSave?(editId!==null?0:Date.now()+300000):0,signature)}
  catch(e){recordRecipeImportAttempt(id,true,Date.now()+300000,signature)}finally{recipeImportInFlight.delete(id)}
 }}
 try{await Promise.all([worker(),worker()])}finally{recipeImportWorkersActive=false;if(recipeImportJobs.size&&!recipePageLeaving&&!recipeBackgroundWritesBlocked())enrichImportedRecipes([])}
}
function requestRecipeImportResume(){if(recipeImportResumeTimer!==null)return;recipeImportResumeTimer=setTimeout(()=>{recipeImportResumeTimer=null;resumeRecipeImports()},0)}
function resumeRecipeImports(){
 if(document.readyState==='loading'||mealPersistence.paused||recipePageLeaving||navigator.onLine===false||recipeBackgroundWritesBlocked())return;
 enrichImportedRecipes(meals.filter(m=>m.recipeImportPending&&(!m.recipeImportRetryAt||m.recipeImportRetryAt<=Date.now())).map(m=>m.id));
}
window.addEventListener('online',resumeRecipeImports);
window.addEventListener('DOMContentLoaded',resumeRecipeImports,{once:true});
new MutationObserver(requestRecipeImportResume).observe(document.body,{childList:true});

function restoreState(state){if(Object.hasOwn(state,'autoMoveUndo')&&typeof restoreAutoMoveState==='function')restoreAutoMoveState(state.autoMoveUndo);if(state.scaleUndo)writeOccurrenceScales(JSON.parse(JSON.stringify(state.scaleUndo)));if(Object.hasOwn(state,'groceryTextUndo')){if(state.groceryTextUndo===null)localStorage.removeItem('mealRotationGroceryTextOverridesV1');else localStorage.setItem('mealRotationGroceryTextOverridesV1',state.groceryTextUndo)}if(Object.hasOwn(state,'groupRotation')){if(state.groupRotation===null)localStorage.removeItem(GROUP_ROTATION_KEY);else localStorage.setItem(GROUP_ROTATION_KEY,state.groupRotation)}if(Array.isArray(state.upNextOrder))localStorage.setItem(UP_NEXT_ORDER_KEY,JSON.stringify(state.upNextOrder));if(state.manualGroceriesUndo)saveManualGroceryItems(state.manualGroceriesUndo);if(Object.hasOwn(state,'plannedMealsUndo')){if(state.plannedMealsUndo===null)localStorage.removeItem('mealRotationPlannedMealsV1');else localStorage.setItem('mealRotationPlannedMealsV1',state.plannedMealsUndo)}if(Object.hasOwn(state,'regularGroceriesUndo')){if(state.regularGroceriesUndo===null)localStorage.removeItem('mealRotationRegularGroceriesV1');else localStorage.setItem('mealRotationRegularGroceriesV1',state.regularGroceriesUndo)}if(state.recipePhotoUndo){try{restoreRecipePhotoReferences(state.recipePhotoUndo.refs)}catch(e){}return}if(state.scheduleChangeUndo)state=restoreScheduleUndoState(state);if(state.groupUndoGrocery)state=restoreGroupGroceryUndo(state);const wasRestoring=restoringRotationCalendars;restoringRotationCalendars=true;try{if(Object.hasOwn(state,'groupIdentities')){if(state.groupIdentities===null)localStorage.removeItem(GROUP_IDENTITIES_KEY);else localStorage.setItem(GROUP_IDENTITIES_KEY,state.groupIdentities)}if(Object.prototype.hasOwnProperty.call(state,'lastRotationBefore')){try{if(state.lastRotationBefore===null)localStorage.removeItem('mealRotationLastRotationBeforeV1');else if(typeof state.lastRotationBefore==='string')localStorage.setItem('mealRotationLastRotationBeforeV1',state.lastRotationBefore)}catch(e){}}if(!restoreMasterGroupOrder(state.masterGroupOrder))return;cats=state.cats;active=state.active;meals=state.meals;if(Array.isArray(state.mealPlans)&&state.mealPlans.length){mealPlans=JSON.parse(JSON.stringify(state.mealPlans));activePlanId=state.activePlanId||mealPlans[0].id;showMealPlanTabs=!!state.showMealPlanTabs;autoPinTopCategories=true;}else saveActiveMealPlan();checkedIngredients=new Set(state.checkedIngredients||[]);groceryOccurrenceChecks=state.groceryOccurrenceChecks?JSON.parse(JSON.stringify(state.groceryOccurrenceChecks)):{version:1,checks:{}};groceryCheckStorageInvalid=false;saveGroceryOccurrenceChecks();if(state.weekdayCategories)weekdayCategories=state.weekdayCategories;if(state.weekdayMealOverrides)weekdayMealOverrides=state.weekdayMealOverrides;if(state.weekdayRecipeFilters){weekdayRecipeFilters=state.weekdayRecipeFilters;saveWeekdayRecipeFilters();}if(state.pinnedCats)pinnedCats=state.pinnedCats;if(state.expandedCats)expandedCats=state.expandedCats;if(typeof state.autoPinTopCategories==='boolean')autoPinTopCategories=true;if(typeof state.applyPinsToAllTabs==='boolean'){applyPinsToAllTabs=state.applyPinsToAllTabs;localStorage.setItem('mealRotationApplyPinsAllTabsV1',String(applyPinsToAllTabs))}if(['all','current','across','none'].includes(state.masterOpenMode))masterOpenMode=state.masterOpenMode;if(typeof state.masterPinsOverride==='boolean')masterPinsOverride=state.masterPinsOverride;saveMasterOpeningPrefs();if(state.startWeekday)startWeekday=state.startWeekday;if(state.topCounts)topCounts=state.topCounts;categoryColors=state.categoryColors&&typeof state.categoryColors==='object'?{...state.categoryColors}:{};saveCategoryColors();weekdayColors=state.weekdayColors&&typeof state.weekdayColors==='object'?{...state.weekdayColors}:deriveWeekdayColors(categoryColors);saveWeekdayColors();id=Math.max(0,...meals.map(m=>Number(m.id)||0))+1;editId=null;newRecipeDraftId=null;editorCategoryBaseline=null;editorDraftCategories=null;stopMealEditorPositioning();menuCat=null;if(state.skippedCookingState)restoreSkippedCookingState(state.skippedCookingState);if(state.bulkRecipeUndoLabels){recipeLabelCatalog=[...state.bulkRecipeUndoLabels];saveRecipeLabelCatalog()}if(state.bulkRecipeUndoSelections)restoreBulkRecipeSelections(state.bulkRecipeUndoSelections);if(state.groupUndoIngredientSelections){const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const [key,value]of Object.entries(state.groupUndoIngredientSelections)){if(value===null)delete selected[key];else selected[key]=value}localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected))}if(state.bulkRecipeUndoNewSelections?.length){const values=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const key of state.bulkRecipeUndoNewSelections)if(!meals.some(m=>String(m.id)===key))delete values[key];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(values))}if(state.bulkRecipeUndoExclusions){for(const key of state.bulkRecipeUndoExclusions)masterGroceryExcludedMealKeys.add(key);saveMasterGroceryMealExclusions()}persist();try{localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));saveWeekdayCategories();saveWeekdayMealOverrides();saveTopCounts();localStorage.setItem('mealRotationPinnedCategoriesV1',JSON.stringify(pinnedCats));localStorage.setItem('mealRotationApplyPinsAllTabsV1',String(applyPinsToAllTabs));localStorage.setItem('mealRotationExpandedCategoriesV1',JSON.stringify(expandedCats));localStorage.setItem('mealRotationStartWeekdayV1',startWeekday);localStorage.setItem('mealRotationAutoPinTopCategoriesV1',String(autoPinTopCategories))}catch(e){}resetGroceriesForNewTopMeals(new Set(getDisplayedWeekdayMeals().map(({meal})=>String(meal.id))));render()}finally{restoringRotationCalendars=wasRestoring}}
// Photos are optional presentation data; recipe and scheduling saves never await reads.
function recipePhotoReferences(ids){return Object.fromEntries(meals.filter(m=>ids.includes(String(m.id))).map(m=>[String(m.id),Object.hasOwn(m,'recipePhotoId')?{present:true,value:m.recipePhotoId}:{present:false}]))}
function restoreRecipePhotoReferences(refs,recordUndo=false,expected=null){
 const ids=Object.keys(refs),prior=recipePhotoReferences(ids);if(expected&&JSON.stringify(prior)!==JSON.stringify(expected))throw Error('The recipe photo changed. Repeat this action with the current recipe.');
 const next=JSON.parse(JSON.stringify(meals));for(const meal of next)if(Object.hasOwn(refs,String(meal.id))){const ref=refs[String(meal.id)];if(ref.present)meal.recipePhotoId=ref.value;else delete meal.recipePhotoId}
 if(JSON.stringify(next)===JSON.stringify(meals))return true;
 const before=JSON.parse(captureState()),storage=recipeBulkBackupAPI.capture();recipeBulkBackupAPI.validate(storage);const core=JSON.parse(storage.mealRotationDataV1);const proposed={...storage,mealRotationDataV1:JSON.stringify({...core,cats,active,meals:next})};recipeBulkBackupAPI.validate(proposed);
 recipeBulkBackupAPI.restore(proposed,{id:'recipe-photo:'+JSON.stringify(ids.sort()),kind:'recipe-photo',ownerId:null,retry:()=>restoreRecipePhotoReferences(refs,recordUndo,expected)});meals=next;
 if(recordUndo){before.recipePhotoUndo={refs:prior};snapshot(JSON.stringify(before))}return true;
}
async function prepareOptionalBackupPhotos(data){let dialog=null;if(data.photos||recipePhotoStorage.refs(data).size){dialog=recipeBulkDialog('Restoring backup');const text=document.createElement('p'),cancel=document.createElement('button');text.textContent='Preparing your backup. Canceling keeps your current recipes.';cancel.type='button';cancel.className='smallbtn';cancel.style.minHeight='44px';cancel.textContent='Cancel backup restore';cancel.onclick=dialog.close;dialog.panel.append(text,cancel);cancel.focus({preventScroll:true})}try{const warnings=await recipePhotoStorage.restore(data);return {warnings,cancelled:!!dialog&&!dialog.overlay.isConnected}}finally{dialog?.close()}}
async function exportRecipeBackup(data,filename='meal-rotation-backup.json'){data=JSON.parse(JSON.stringify(data));let result=data;try{result=await recipePhotoStorage.appendBackup(data)}catch(e){result={...data,photos:{version:1,items:[],missing:[...recipePhotoStorage.refs(data)],warnings:['Photo export failed. Recipes are still backed up.']}}}let blob;try{blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'})}catch(e){result={...data,photos:{version:1,items:[],missing:[...recipePhotoStorage.refs(data)],warnings:['Photo encoding failed; recipe data is still backed up.']}};blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'})}const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);if(result.photos?.warnings?.length)showAppMessage('Recipe backup downloaded. Some optional photos were unavailable: '+result.photos.warnings.join(' '))}


function recipeImportNotice(message,reviewMeals=[]){
 if(mealPersistence.unsaved)message='Changes are only in memory and have not been saved. Use Retry Save before closing this page. '+message;
 const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:16500;display:flex;align-items:center;justify-content:center;padding:18px';
 const panel=document.createElement('div');panel.setAttribute('role','alertdialog');panel.setAttribute('aria-modal','true');panel.style.cssText='width:100%;max-width:450px;padding:22px;background:white;color:#242424;border-radius:14px;box-shadow:0 12px 35px #0003';
 const msg=document.createElement('p');msg.textContent=message;msg.style.cssText='font-size:17px;margin:0 0 22px';
 const ok=document.createElement('button');ok.type='button';ok.className='smallbtn';ok.textContent='OK';ok.style.cssText='display:block;margin-left:auto;min-width:90px;padding:10px 18px';ok.onclick=()=>overlay.remove();
 panel.append(msg);if(reviewMeals.length){const review=document.createElement('button');review.type='button';review.className='smallbtn';review.textContent='Review related recipes';review.onclick=()=>{overlay.remove();openRecipeImportReview(reviewMeals,false)};panel.append(review)}panel.append(ok);overlay.append(panel);if(recipeViewer)overlay.style.zIndex='31001';document.body.append(overlay);
}
/* Multi-source recipe importer. All files are parsed locally; imports require review. */
function recipeImportCsvRows(text){
 const rows=[];let row=[],cell='',quoted=false;
 text=String(text||'').replace(/^\ufeff/,'');
 for(let i=0;i<text.length;i++){const ch=text[i];if(quoted){if(ch==='"'&&text[i+1]==='"'){cell+='"';i++}else if(ch==='"')quoted=false;else cell+=ch}
 else if(ch==='"')quoted=true;else if(ch===','){row.push(cell);cell=''}else if(ch==='\n'||ch==='\r'){if(ch==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(x=>x.trim()))rows.push(row);row=[];cell=''}else cell+=ch}
 row.push(cell);if(row.some(x=>x.trim()))rows.push(row);return rows;
}
function recipeImportCsv(text){
 const rows=recipeImportCsvRows(text);if(rows.length<2)return [];
 const headers=rows.shift().map(x=>x.toLowerCase().replace(/[^a-z0-9]/g,''));
 const get=(cells,...keys)=>{for(const k of keys){const i=headers.indexOf(k);if(i>=0&&String(cells[i]??'').trim())return String(cells[i]).trim()}return ''};
 if(!headers.some(x=>['name','title','recipename','recipe'].includes(x)))return [];
 return rows.map(cells=>({name:get(cells,'name','title','recipename','recipe'),recipeCategory:get(cells,'groups','category','tags','labels','recipecategory'),recipeIngredient:get(cells,'ingredients','recipeingredient','ingredientlist','ingredient'),prepTime:get(cells,'preptime','preparationtime','prepminutes'),cookTime:get(cells,'cooktime','cookingtime','cookminutes'),totalTime:get(cells,'totaltime','duration','totalminutes'),url:get(cells,'url','recipeurl','link','sourceurl','source','website'),identifier:get(cells,'id','recipeid','uuid'),linkedRecipes:get(cells,'linkedrecipes','linkedmeals','relatedrecipes','relatedmeals'),recipeInstructions:get(cells,'instructions','directions','method','steps','recipeinstructions'),notes:get(cells,'notes','recipenotes'),marinateTime:get(cells,'marinatetime','marinatingtime','marinate')})).filter(x=>x.name);
}
function recipeImportHtml(text){
 const doc=new DOMParser().parseFromString(text,'text/html'),found=[];
 doc.querySelectorAll('script[type="application/ld+json"]').forEach(script=>{try{found.push(...recipeImportItems(JSON.parse(script.textContent)))}catch(e){}});
 return mergeRecipeCardInstructions(found,recipeCardRecords(doc));
}
function recipeImportTrelloBoard(board){
 const lists=new Map((board.lists||[]).map(x=>[x.id,x.name]));
 const labels=new Map((board.labels||[]).map(x=>[x.id,x.name]));
 const checks=new Map();for(const cl of board.checklists||[]){if(!checks.has(cl.idCard))checks.set(cl.idCard,[]);checks.get(cl.idCard).push(...(cl.checkItems||[]).map(x=>x.name).filter(Boolean))}
 return (board.cards||[]).filter(c=>!c.closed&&c.name&&c.name.trim()).map(c=>{
  const tags=[...(c.labels||[]).map(x=>typeof x==='string'?labels.get(x):x.name).filter(Boolean),...(c.idLabels||[]).map(x=>labels.get(x)).filter(Boolean)];
  const list=lists.get(c.idList);if(list)tags.push('Trello list: '+list);
  const desc=String(c.desc||'');
  const descItems=[];let reading=false;
  for(const line of desc.split(/\r?\n/)){const t=line.trim();if(/^#{0,3}\s*(?:ingredients|ingredient list)\s*:?\s*$/i.test(t)){reading=true;continue}if(reading&&/^(?:#{1,3}\s*)?(?:instructions|directions|steps|method)\s*:?\s*$/i.test(t))break;
   if(reading&&/^[-*•]\s+(?:\[[ xX]\]\s*)?\S/.test(t))descItems.push(t.replace(/^[-*•]\s+(?:\[[ xX]\]\s*)?/,''));}
  const allIngredients=checks.get(c.id)||descItems;
  const website=(desc.match(/https?:\/\/[^\s)\]>]+/i)||[])[0]||'';
  const url=(c.shortUrl||c.url||website||'');
  const recipeSections=recipeTextSections(desc);
  return {recipeImportReferences:recipeSections.recipeImportReferences,recipeInstructions:recipeSections.instructions,notes:recipeSections.notes,name:c.name,recipeCategory:[...new Set(tags)],recipeIngredient:allIngredients,identifier:'trello:'+String(c.id),url,sourceUrl:website,importSourceId:'trello:'+String(c.id)};
 });
}
function recipeImportItems(json){
 if(!json||typeof json!=='object')return [];
 if(!json.name&&!json.title){if(json.recipe&&typeof json.recipe==='object')return recipeImportItems(json.recipe);if(json.data&&typeof json.data==='object')return recipeImportItems(json.data);if(json.recipes&&!Array.isArray(json.recipes)&&typeof json.recipes==='object')return recipeImportItems(Object.values(json.recipes));}
 if(Array.isArray(json.cards)&&Array.isArray(json.lists))return recipeImportTrelloBoard(json);
 const resolveInstructions=recipeInstructionReferenceResolver(json);
 const raw=Array.isArray(json)?json:json.version===2&&Array.isArray(json.meals)?json.meals:Array.isArray(json.recipes)?json.recipes:json.recipes===undefined&&Array.isArray(json.meals)?json.meals:Array.isArray(json['@graph'])?json['@graph']:Array.isArray(json.items)?json.items:[json];
 return raw.filter(x=>x&&typeof x==='object'&&!Array.isArray(x)).flatMap(r=>{
  if(r['@graph'])return recipeImportItems(r);
  const name=String(r.name||r.title||r.recipeName||'').trim();if(!name)return [];
  if(r['@type']&&!String(Array.isArray(r['@type'])?r['@type'].join(' '):r['@type']).toLowerCase().includes('recipe'))return [];
  return [{...r,name,recipeInstructions:resolveInstructions(recipeImportInstructionValue(r)),recipeCategory:recipeImportTags(r),recipeIngredient:r.recipeIngredient??r.ingredients??[],prepTime:r.prepTime??r.prep_time??r.preparationTime??'',cookTime:r.cookTime??r.cook_time??'',totalTime:r.totalTime??r.total_time??'',url:r.url||r.recipeUrl||r.link||r.source_url||r.sourceUrl||'',identifier:r.identifier||r.id||r.uid||r.uuid||'',linkedRecipes:r.linkedRecipes??r.linkedMeals??r.linkedRecipeIds??r.linkedMealIds??r.relatedRecipes??r.relatedMeals??[],importSourceId:r.importSourceId||(r.uid?'paprika:'+r.uid:r.title&&r.id?'mela:'+r.id:'')}];
 });
}
function recipeImportTags(r){
 return [...new Set([r.recipeCategory,r.categories,r.cat,r.tags,r.labels,r.keywords].flatMap(values=>Array.isArray(values)?values:typeof values==='string'?values.split(/[,;|]/):[])
  .map(x=>typeof x==='string'?x.trim():x&&typeof x==='object'?String(x.name||x.label||'').trim():'').filter(Boolean))];
}
function recipeImportMinutes(value){
 if(value===undefined||value===null||value==='')return '';
 if(typeof value==='number')return Number.isFinite(value)&&value>=0?Math.round(value):'';
 const s=String(value).trim().toUpperCase();
 const iso=s.match(/^P(?:(\d+(?:\.\d+)?)D)?(?:T(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?)?$/);
 if(iso){const minutes=(Number(iso[1]||0)*1440)+(Number(iso[2]||0)*60)+Number(iso[3]||0)+Number(iso[4]||0)/60;return minutes>0?Math.round(minutes):'';}
 const hrs=s.match(/(\d+(?:\.\d+)?)\s*(?:HOURS?|HRS?|HR|H)\b/),mins=s.match(/(\d+(?:\.\d+)?)\s*(?:MINUTES?|MINS?|MIN|M)\b/);
 if(hrs||mins)return Math.round(Number(hrs?.[1]||0)*60+Number(mins?.[1]||0));
 return /^\d+$/.test(s)?Number(s):'';
}
// Use the RecipeSage share URL format, including for previously imported legacy links.
const recipeSageUuidPattern=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function recipeSageShareUrl(recipeId){return 'https://android.recipesage.com/api/share/recipe/'+encodeURIComponent(recipeId)}
function correctedRecipeSageUrl(meal){
 const old=String(meal.url||'').trim();
 const legacy=old.match(/^https?:\/\/(?:www\.)?recipesage\.com\/app\/recipes\/([0-9a-f-]{36})(?:[/?#].*)?$/i);
 if(legacy&&recipeSageUuidPattern.test(legacy[1]))return recipeSageShareUrl(legacy[1]);
 // An existing, unrelated recipe URL should not be replaced.
 if(old)return old;
 const recipeId=String(meal.recipeSageId||meal.importSourceId||'').trim();
 return recipeSageUuidPattern.test(recipeId)?recipeSageShareUrl(recipeId):old;
}
function repairImportedRecipeSageLinks(){
 for(const meal of meals){const corrected=correctedRecipeSageUrl(meal);if(corrected!==meal.url)meal.url=corrected;}
}
function recipeImportUrl(r){
 const safe=v=>typeof v==='string'&&/^https?:\/\//i.test(v.trim())?v.trim():'';
 const direct=safe(r.url)||safe(r.mainEntityOfPage)||safe(r.recipeUrl);
 if(direct)return correctedRecipeSageUrl({url:direct});
 const sourceId=String(r.identifier||'').trim();
 if(recipeSageUuidPattern.test(sourceId))return recipeSageShareUrl(sourceId);
 return safe(r.isBasedOn)||safe(r.sourceUrl)||'';
}
function recipeImportSourceUrl(r){const u=r.isBasedOn||r.sourceUrl||'';return typeof u==='string'&&/^https?:\/\//i.test(u.trim())?u.trim():''}
function recipeImportIngredients(r){
 const raw=r.recipeIngredient??r.ingredients??[];
 return (Array.isArray(raw)?raw:typeof raw==='string'?raw.split(/\r?\n/):[])
  .map(x=>typeof x==='string'?x:typeof x==='object'&&x?String(x.text||[x.quantity??x.amount??x.value,x.unit||x.unitText||x.unitCode,x.name||x.ingredient].filter(v=>v!==undefined&&v!==null&&String(v).trim()).join(' ')||''):'')
  .map(x=>x.replace(/^\s*[-*•]\s*(?:\[[ xX]\]\s*)?/,'').replace(/\s+/g,' ').trim()).filter(Boolean);
}
function recipeImportIdentity(r){
 const original=String(r.importSourceId||r.identifier||r['@id']||'').trim();if(original)return original;
 const stable=(r.name||'').trim().toLowerCase()+'|'+recipeImportUrl(r).toLowerCase()+'|'+recipeImportIngredients(r).join(';').toLowerCase();
 let h=2166136261;for(let i=0;i<stable.length;i++)h=Math.imul(h^stable.charCodeAt(i),16777619);return 'recipe-file:'+String(h>>>0);
}
async function recipeImportZip(file){
 const bytes=new Uint8Array(await file.arrayBuffer());const view=new DataView(bytes.buffer);
 const u16=i=>view.getUint16(i,true),u32=i=>view.getUint32(i,true);
 let eocd=-1;for(let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--){if(u32(i)===0x06054b50){eocd=i;break}}
 if(eocd<0)throw new Error('Invalid ZIP export.');
 const count=u16(eocd+10),directory=u32(eocd+16);
 if(count>2500)throw new Error('Archive has too many files. Split it into smaller exports.');
 let cursor=directory,recipes=[],processed=0,totalSize=0;
 async function decompress(data,format){
  if(typeof DecompressionStream!=='function')throw new Error('This browser cannot decompress recipe archives.');
  const stream=new Blob([data]).stream().pipeThrough(new DecompressionStream(format));return new Uint8Array(await new Response(stream).arrayBuffer());
 }
 const decoder=new TextDecoder();
 for(let n=0;n<count;n++){
  if(cursor+46>bytes.length||u32(cursor)!==0x02014b50)throw new Error('Damaged ZIP export.');
  const method=u16(cursor+10),packed=u32(cursor+20),unpacked=u32(cursor+24),nameLen=u16(cursor+28),extraLen=u16(cursor+30),commentLen=u16(cursor+32),local=u32(cursor+42);
  const name=decoder.decode(bytes.subarray(cursor+46,cursor+46+nameLen));cursor+=46+nameLen+extraLen+commentLen;
  const lower=name.toLowerCase();
  if(name.endsWith('/')||/(^|\/)__macosx\//i.test(name)||/(^|\/)\._/.test(name)||! /\.(?:json|jsonld|melarecipe|paprikarecipe|html|htm|csv)$/.test(lower))continue;
  if(++processed>2000||unpacked>12000000||(totalSize+=unpacked)>60000000)throw new Error('Archive is too large to import safely.');
  if(local+30>bytes.length||u32(local)!==0x04034b50)throw new Error('Damaged ZIP recipe entry.');
  const dataOffset=local+30+u16(local+26)+u16(local+28);
  if(dataOffset+packed>bytes.length)throw new Error('Incomplete ZIP export.');
  const packedBytes=bytes.slice(dataOffset,dataOffset+packed);
  let contentBytes;
  try{contentBytes=method===0?packedBytes:method===8?await decompress(packedBytes,'deflate-raw'):null;
   if(!contentBytes)continue;
   if(lower.endsWith('.paprikarecipe')&&contentBytes[0]===0x1f&&contentBytes[1]===0x8b)contentBytes=await decompress(contentBytes,'gzip');
   const content=decoder.decode(contentBytes);
   if(/\.(?:json|jsonld|melarecipe|paprikarecipe)$/.test(lower))recipes.push(...recipeImportItems(JSON.parse(content)));
   else if(/\.csv$/.test(lower))recipes.push(...recipeImportCsv(content));
   else recipes.push(...recipeImportHtml(content));
  }catch(e){if(String(e.message||'').includes('decompress'))throw e;/* Non-recipe metadata can share these extensions. */}
 }
 return recipes;
}
async function recipeImportReadFile(file){
 const name=file.name.toLowerCase();
 if(/\.(?:zip|paprikarecipes|melarecipes)$/.test(name))return recipeImportZip(file);
 let text;
 if(/\.paprikarecipe$/.test(name)){const bytes=new Uint8Array(await file.arrayBuffer());if(bytes[0]===0x1f&&bytes[1]===0x8b){if(typeof DecompressionStream!=='function')throw Error('This browser cannot decompress Paprika recipes.');text=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text()}else text=new TextDecoder().decode(bytes)}else text=await file.text();
 if(/\.csv$/.test(name))return recipeImportCsv(text);
 if(/\.html?$/.test(name))return recipeImportHtml(text);
 if(/\.(?:json|jsonld|melarecipe|paprikarecipe)$/.test(name))return recipeImportItems(JSON.parse(text));
 throw new Error('Unsupported file type. Use JSON-LD, JSON, CSV, HTML, ZIP, Paprika, or Mela export.');
}
// Existing app exports retain saved status; other sources keep the importer's default.
function recipeImportStatus(record,defaultRotation){
 const legacy=String(record.recipeStatus??record.status??'').trim().toLowerCase();
 const named={'ideas':'back-burner','back burner':'back-burner','back-burner':'back-burner','up next':'up-next','up-next':'up-next','in rotation':'rotation','rotation':'rotation','regulars':'rotation','regular':'rotation','off menu':'back-burner','off-menu':'back-burner'}[legacy];
 const status=named||(typeof record.rotation==='boolean'?(record.rotation?'rotation':'back-burner'):null);
 return status?{recipeStatus:status==='rotation'?'rotation':'up-next',upNextStar:typeof record.upNextStar==='boolean'?record.upNextStar:status==='up-next',rotation:status==='rotation',keepAsIdea:status!=='rotation'}:{rotation:defaultRotation,upNextStar:false,keepAsIdea:!defaultRotation};
}
function showRecipeImportSelection(items,filename){
 const sideChoices=new Set(),side=builtinSidesGroup();
 const tags=[...new Set(items.flatMap(recipeImportTags))].sort((a,b)=>a.localeCompare(b,undefined,{sensitivity:'base'}));
 const dialog=recipeImportDialog('Choose meal groups'),overlay=dialog.overlay,box=dialog.panel;overlay.id='recipeImportDialog';box.replaceChildren();
 const title=document.createElement('h2');title.id='recipeImportTitle';title.textContent='Choose meal groups';title.style.cssText='font-size:21px;margin:0;display:flex;justify-content:space-between;align-items:center';const close=document.createElement('button');close.type='button';close.className='iconbtn';setIconButton(close,'cancel','Close import review');close.onclick=()=>dialog.close();title.append(close);box.append(title);
 const subtitle=document.createElement('p');subtitle.textContent=items.length+' recipes found. Choose which groups to import.';subtitle.style.cssText='font-size:14px;color:#666;margin:0';box.append(subtitle);
 const summary=document.createElement('p');summary.style.cssText='font-size:13px;color:#666;margin:0';box.append(summary);
 const toolbar=document.createElement('div');toolbar.className='bulk-import-selection';toolbar.style.cssText='display:flex;gap:8px;align-items:center';
 const all=document.createElement('button');all.type='button';all.className='iconbtn';all.innerHTML=grocerySelectionIcon(true);all.title='Select all groups';all.setAttribute('aria-label',all.title);
 const none=document.createElement('button');none.type='button';none.className='iconbtn';none.innerHTML=grocerySelectionIcon(false);none.title='Deselect all groups';none.setAttribute('aria-label',none.title);
 toolbar.append(all,none);box.append(toolbar);
 const list=document.createElement('div');list.style.cssText='padding:6px 2px;border-top:1px solid #e5e5e5;border-bottom:1px solid #e5e5e5';const checks=[];
 for(const tag of tags){const row=document.createElement('label');row.style.cssText='display:flex;align-items:center;gap:10px;padding:9px 4px;font-size:16px';const cb=document.createElement('input');cb.type='checkbox';cb.checked=false;cb.style.cssText='width:21px;height:21px;flex:0 0 21px';const name=document.createElement('span');name.textContent=tag;name.style.flex='1';const count=document.createElement('span');count.textContent=String(items.filter(x=>recipeImportTags(x).includes(tag)).length);count.style.cssText='font-size:12px;color:#888';row.append(cb,name,count);list.append(row);checks.push({tag,cb});cb.onchange=updateSummary;}
 if(!tags.length){list.textContent='This file has no recipe tags. All imported meals will go into Unassigned.';list.style.fontSize='14px';all.disabled=true;none.disabled=true;}
 box.append(list);bindSelectAllState(all,none,()=>checks.map(c=>c.cb));
 const sideReview=document.createElement('fieldset');sideReview.className='import-side-review';const sideLegend=document.createElement('legend');sideLegend.textContent='Likely side recipes — add to Sides?';sideReview.append(sideLegend);
 for(const recipe of items.filter(recipeImportLikelySide)){const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.onchange=()=>{if(check.checked)sideChoices.add(recipe);else sideChoices.delete(recipe);updateSummary()};label.append(check,document.createTextNode(recipe.name));sideReview.append(label)}
 if(side&&sideReview.querySelector('input'))box.append(sideReview);

 const notes=document.createElement('p');notes.style.cssText='font-size:13px;color:#666;margin:0';notes.textContent='Checked source tags become meal groups. Meals without a checked group or Sides selection go to Unassigned.';box.append(notes);const importRotation=document.createElement('input');importRotation.type='checkbox';importRotation.checked=true;stage2FormField(box,'Add grouped imports to rotation',importRotation);
 const footer=document.createElement('div');footer.style.cssText='display:flex;justify-content:flex-end;gap:10px;margin-top:6px';
 const cancel=document.createElement('button');cancel.type='button';cancel.className='smallbtn';cancel.textContent='Cancel';
 const apply=document.createElement('button');apply.type='button';apply.className='smallbtn';apply.textContent='Import recipes';apply.style.cssText='background:#e8eefb;border-color:#aac0df;font-weight:600';
 footer.append(cancel,apply);box.append(footer);
 overlay.classList.add('bulk-recipe-import');const viewportLimit=box.style.maxHeight;box.style.cssText='display:flex;flex-direction:column;overflow:hidden;gap:10px';box.style.maxHeight=viewportLimit||'calc(100dvh - 36px)';
 const content=document.createElement('div');content.className='bulk-import-body';for(const child of [...box.children])if(child!==title&&child!==footer)content.append(child);box.replaceChildren(title,content,footer);footer.className='bulk-import-footer';
 function updateSummary(){const chosen=new Set(checks.filter(x=>x.cb.checked).map(x=>x.tag));const unassigned=items.filter(x=>!sideChoices.has(x)&&!recipeImportTags(x).some(t=>chosen.has(t))).length;summary.textContent=chosen.size+' groups selected · '+unassigned+' recipe'+(unassigned===1?'':'s')+' will go into Unassigned';}
 all.onclick=()=>{checks.forEach(x=>x.cb.checked=true);updateSummary()};none.onclick=()=>{checks.forEach(x=>x.cb.checked=false);updateSummary()};cancel.onclick=()=>dialog.close();overlay.onclick=e=>{if(e.target===overlay)dialog.close()};
 apply.onclick=()=>{
  const chosen=new Set(checks.filter(x=>x.cb.checked).map(x=>x.tag));
  const normalize=x=>String(x||'').trim().toLocaleLowerCase();
  const nextCats=[...cats],newMeals=meals.map(m=>({...m})),addedCats=[];const enrichIds=[];
  const canonicalLabels=new Map(allRecipeLabels().map(name=>[labelKey(name),name]));
  const existingIds=new Set(meals.map(m=>String(m.importSourceId||'')).filter(Boolean));
  let nextId=id,added=0,skipped=0,enriched=0,unassigned=0,firstCategory='';
  const catFor=tag=>{const key=normalize(tag);let cat=nextCats.find(c=>normalize(c)===key);if(!cat){cat=tag.charAt(0).toUpperCase()+tag.slice(1);nextCats.push(cat);addedCats.push(cat)}return cat};
  for(const r of items){
   const sourceId=recipeImportIdentity(r);
   if(sourceId&&existingIds.has(sourceId)){const details=completeRecipeFields(r);for(const m of newMeals.filter(m=>m.importSourceId===sourceId))if(fillMissingRecipeContent(m,details))enriched++;skipped++;continue;}
   const matching=recipeImportTags(r).filter(t=>chosen.has(t));
   const categories=[...new Set([...matching.map(catFor),...(side&&sideChoices.has(r)?[side]:[])])];
   if(!categories.length){categories.push('');unassigned++}
   if(!firstCategory)firstCategory=categories[0];
   const prep=recipeImportMinutes(r.prepTime??r.activeTime);
   const total=recipeImportMinutes(r.totalTime);
   const cook=recipeImportMinutes(r.cookTime);
   const importedLabels=[...new Set(recipeImportTags(r).map(tag=>{const key=labelKey(tag);if(!canonicalLabels.has(key))canonicalLabels.set(key,tag.trim().replace(/\s+/g,' '));return canonicalLabels.get(key)}))];
   const importedDetails=completeRecipeFields(r);
   const base={recipeImportReferences:importedDetails.recipeImportReferences,recipeImportPending:!importedDetails.instructions.some(b=>b.type==='step')&&!!(recipeImportUrl(r)||importedDetails.originalRecipeUrl),instructions:importedDetails.instructions,notes:importedDetails.notes,originalRecipeUrl:importedDetails.originalRecipeUrl,name:r.name.trim(),labels:importedLabels,...recipeImportStatus(r,importRotation.checked),groceryDefaultAll:true,prep,cook,total:total!==''?total:(prep!==''&&cook!==''?Number(prep)+Number(cook):''),marinate:importedDetails.marinate,url:recipeImportUrl(r),sourceUrl:recipeImportSourceUrl(r),recipeSageId:/^[0-9a-f]{8}-/.test(sourceId)?sourceId:'',importSourceId:sourceId,ingredients:importedDetails.ingredients};
   const group=categories.length>1?'imported-'+(sourceId||nextId):'';
   categories.forEach(cat=>{const meal={...base,id:nextId++,cat,linkGroup:group,ingredients:[...base.ingredients]};if(!cat){meal.rotation=false;meal.keepAsIdea=true}newMeals.push(meal);enrichIds.push(meal.id)});
   if(sourceId)existingIds.add(sourceId);
   added++;
  }
  if(!added&&!enriched){dialog.close();recipeImportNotice('All recipes in this file have already been imported.');return}
  const nextActive=firstCategory||active;
  const encoded=JSON.stringify({cats:nextCats,active:nextActive,meals:newMeals});
  try{localStorage.setItem('mealRotationDataV1',encoded)}catch(err){
   recipeImportNotice('Import could not be saved. Your browser may be low on storage. No existing meals were changed.');return;
  }
  snapshot();cats=nextCats;meals=newMeals;id=nextId;recipeLabelCatalog=[...canonicalLabels.values()];saveRecipeLabelCatalog();active=nextActive;showTop=false;editId=null;menuCat=null;
  expandedCats=[...new Set([...expandedCats,...addedCats])];
  try{localStorage.setItem('mealRotationExpandedCategoriesV1',JSON.stringify(expandedCats))}catch(e){}
  if(unassigned){masterExpansionInitialized=true;masterExpandedCategories.add('')}
  dialog.navigate=true;dialog.close();render();
  recipeImportNotice('Imported '+added+' recipes across '+addedCats.length+' new groups.'+(unassigned?' '+unassigned+' saved in Unassigned.':'')+(enriched?' Added missing details to '+enriched+' existing recipe records.':'')+(skipped?' Skipped '+skipped+' duplicate recipes.':'')+(enrichIds.some(id=>!instructionBlocks(meals.find(m=>m.id===id)?.instructions).some(b=>b.type==='step'))?' Some imports have no reliable cooking instructions yet. Available ingredients were preserved. Supported source URLs will be checked in the background; review any still incomplete recipes before using them.':''),meals.filter(m=>m.recipeImportReferences?.length&&(enrichIds.includes(m.id)||items.some(r=>recipeImportIdentity(r)===m.importSourceId))));
  enrichImportedRecipes(enrichIds);
 };
 updateSummary();
}
// Explicit, previewed instructions/notes repair. No imports, inferred meals or background writes.
function recipeRepairEmpty(value){
 if(value==null)return true;
 if(typeof value==='string')return !value.trim();
 if(Array.isArray(value))return value.every(recipeRepairEmpty);
 // Preserve unknown objects, headings, placeholders and deliberately written text.
 return !!value&&['step','section'].includes(value.type)&&typeof value.text==='string'&&!value.text.trim()&&Object.keys(value).every(k=>['type','text'].includes(k));
}
function recipeRepairIds(record,source=false){
 const ids=[record.importSourceId,record.recipeSageId,...(source?[record.identifier,record['@id'],recipeImportIdentity(record)]:[])].filter(v=>typeof v==='string'&&v.trim()).map(v=>recipeSageUuidPattern.test(v.trim())?v.trim().toLowerCase():v.trim());
 for(const value of [record.url,record.originalRecipeUrl,record.sourceUrl,record.ingredientImportUrl]){
  const url=correctedRecipeSageUrl({url:String(value||'')}),match=url.match(/^https?:\/\/android\.recipesage\.com\/api\/share\/recipe\/([^/?#]+)(?:[/?#]|$)/i);if(match&&recipeSageUuidPattern.test(match[1]))ids.push(match[1].toLowerCase());
 }
 return [...new Set(ids)];
}
function recipeRepairUrls(record){
 return [record.url,record.originalRecipeUrl,record.sourceUrl,record.source_url,record.ingredientImportUrl,record.isBasedOn].filter(v=>typeof v==='string').map(v=>{try{const u=new URL(v);return ['http:','https:'].includes(u.protocol)?u.href:''}catch(e){return ''}}).filter(Boolean);
}
function recipeMissingInstructionPlan(items,library=meals){
 const equalIngredients=(a,b)=>{const normalize=xs=>recipeImportIngredients(xs).map(x=>recipeReferenceTitle(x)).filter(Boolean);const x=normalize(a),y=normalize(b);return x.length>0&&JSON.stringify(x)===JSON.stringify(y)};
 const sources=items.map(r=>({raw:r,ids:recipeRepairIds(r,true),urls:recipeRepairUrls(r),title:recipeReferenceTitle(r.name||r.title)}));
 const rows=library.map(meal=>{
  const row={meal,reason:'',instructions:null,match:false};
  if(!recipeRepairEmpty(meal.instructions)){row.reason='Already has instructions or other instruction text; preserved.';return row}
  const ids=recipeRepairIds(meal),urls=recipeRepairUrls(meal),title=recipeReferenceTitle(meal.name);
  if(!ids.length&&!meal.sourceUrl&&!meal.ingredientImportUrl&&meal.recipeImportPending===undefined&&meal.recipeImportReferences===undefined){row.reason='No saved import provenance; blank instructions left unchanged.';return row}
  const byId=sources.filter(s=>s.ids.some(id=>ids.includes(id)));
  const matches=byId.length?byId:sources.filter(s=>s.urls.some(url=>urls.includes(url))&&s.title===title&&equalIngredients(meal,s.raw)&&(!ids.length||!s.ids.length));
  if(matches.length!==1){row.reason=matches.length?'Ambiguous file matches; skipped.':'No confident file match; skipped.';return row}
  const source=matches[0];
  const derivedOnly=byId.length&&ids.filter(x=>source.ids.includes(x)).every(x=>x.startsWith('recipe-file:'));
  if(derivedOnly?!(source.title===title&&equalIngredients(meal,source.raw)):!(source.title===title||equalIngredients(meal,source.raw))){row.reason='Identifier matched but recipe details disagree; skipped.';return row}
  const realIds=ids.filter(x=>!x.startsWith('recipe-file:')),otherIds=source.ids.filter(x=>!x.startsWith('recipe-file:'));
  if(realIds.length&&otherIds.length&&realIds.some(x=>!otherIds.includes(x))){row.reason='Conflicting source identifiers; skipped.';return row}
  row.match=true;row.source=source.raw;row.method=byId.length?'Saved source identifier + corroborating recipe details':'Exact source URL + title + ingredients';
  const same=library.filter(m=>m!==meal&&(ids.length?recipeRepairIds(m).some(x=>ids.includes(x)):recipeRepairUrls(m).some(x=>urls.includes(x))&&recipeReferenceTitle(m.name)===title));
  if(same.some(m=>!meal.linkGroup||m.linkGroup!==meal.linkGroup)){row.match=false;row.reason='Several unrelated saved records share this identity; skipped.';return row}
  if(meal.ingredientStepLinks!=null&&(!Array.isArray(meal.ingredientStepLinks)||meal.ingredientStepLinks.length)){row.reason='Existing instruction associations need manual review; preserved.';return row}
  if(Object.values(cookingSessions.occurrences).some(s=>s.context.mealId===String(meal.id)&&s.steps.length)){row.reason='Saved instruction progress needs manual review; preserved.';return row}
  const raw=source.raw.recipeInstructions??source.raw.instructions??source.raw.directions??source.raw.method??source.raw.steps;
  const cleaned=cleanupRecipeInstructions(raw,{conservative:true});
  if(!cleaned.instructions.some(b=>b.type==='step'&&b.text.trim())){row.reason='The file has no usable cooking instructions; skipped.';return row}
  row.instructions=cleaned.instructions;row.removed=cleaned.removed;row.reason='Ready to restore missing instructions only.';return row;
 });
 return {rows,ready:rows.filter(r=>r.instructions),matched:rows.filter(r=>r.match).length,ambiguous:rows.filter(r=>/^(?:Ambiguous|Several unrelated)/.test(r.reason)).length};
}
// Legacy-only recognition: never run the broad import cleaner over saved edits.
function recipeRepairImported(meal){return recipeRepairIds(meal).length>0||!!meal.sourceUrl||!!meal.ingredientImportUrl||meal.recipeImportPending!==undefined||meal.recipeImportReferences!==undefined}
function recipeRepairLegacyLine(raw){
  let text=normalizeRecipeText(raw),links=[];
  if(/<a\b/i.test(raw)){const doc=new DOMParser().parseFromString(raw,'text/html');links=[...doc.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))}
  text=text.replace(/\[([^\]]+)\]\(<?([^\s)>]+)>?\)/g,(_,label,url)=>{links.push(url);return label});
  text=text.trim().replace(/^(?:(?:step\s+)?\d+[.)]\s+|\*\*\d+\*\*\s*|[-*•]\s+)/i,'').replace(/^[*_]+|[*_]+$/g,'').replace(/^#{1,6}\s+/,'').trim();
  return {text,links};
}
function recipeRepairAccountUrl(url){
  try{const absolute=new URL(url);if(!['http:','https:'].includes(absolute.protocol)||!/^(?:www\.|android\.)?recipesage\.com$/i.test(absolute.hostname))return false;return /^\/(?:app\/)?(?:login|register|sign[-_]?up|sign[-_]?in|auth|account)(?:[/?#]|$)/i.test(absolute.pathname)||/^#\/?(?:login|register|sign[-_]?up|sign[-_]?in|auth|account)(?:[/?#]|$)/i.test(absolute.hash)}catch(e){return /^(?:#\/|\/)(?:login|register|sign[-_]?up|sign[-_]?in|auth|account)(?:[/?#]|$)/i.test(url)}
}
function recipeRepairBoilerplate(text,links=[]){
  if(links.length&&!links.every(recipeRepairAccountUrl))return '';
  const prompt=/^(?:create (?:an? |your )?(?:free )?account(?:\s+or\s+(?:login|log in|sign in))?|register(?:\s*(?:\/|or)\s*(?:login|log in|sign in))?|sign up|login|log in|sign in)(?:\s+to\s+(?:(?:save|share|view|edit|rate)\s+(?:this |the |your )?recipe(?:\s+to\s+your\s+collection)?|save))?[.!]?$/i;
  if(prompt.test(text)||(recipeRepairAccountUrl(text)&&!links.length))return 'account';
  if(/^(?:created(?: on| at)?|(?:(?:last[ -]*)?(?:edited|updated|modified)|last[ -]*made)(?: on| at)?|date created|datePublished|dateModified)\s*:?\s*(?:\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})(?:[T, ]+(?:at\s+)?\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:\s*(?:AM|PM))?(?:\s*(?:Z|UTC|[+-]\d{2}:?\d{2}))?)?[.]?$/i.test(text))return 'timestamp';
  if(/^(?:advertisement|sponsored|jump to recipe|print recipe|pin recipe|subscribe to our newsletter|all rights reserved|privacy policy|terms of service|leave a reply|rate this recipe|share on (?:facebook|pinterest|twitter))$/i.test(text))return 'website';
  return '';
}
function recipeRepairLegacyCleanup(meal,library=meals,allowWeb=false){
 const result={instructions:null,removed:[],uncertain:[],reason:''};if(recipeRepairEmpty(meal.instructions))return result;
 if(!recipeRepairImported(meal)&&!(allowWeb&&recipeRepairUrls(meal).length&&importedInstructionBlocks(meal.instructions).some(block=>String(block.text).split(/\r?\n/).some(line=>{const parsed=recipeRepairLegacyLine(line);return recipeRepairBoilerplate(parsed.text,parsed.links)==='account'}))))return result;
 const units=[],DROP=Symbol('removed instruction');
 const visit=(value,section=false)=>{
  if(typeof value==='string'){
   const entries=(value.match(/[^\r\n]*(?:\r\n|\r|\n|$)/g)||[]).filter(Boolean).map(raw=>{
    const line=raw.replace(/(?:\r\n|\r|\n)$/,''),plain=recipeRepairLegacyLine(line),unit={raw,line,text:plain.text,links:plain.links,kind:section?'section':instructionBlocks(line)[0]?.type||'step',remove:recipeRepairBoilerplate(plain.text,plain.links)};units.push(unit);return unit;
   });
   return ()=>{const kept=entries.filter(u=>!u.remove).map(u=>u.raw).join('');return value.trim()&&!kept.trim()?DROP:kept};
  }
  if(Array.isArray(value)){const children=value.map(v=>visit(v));return ()=>children.map(fn=>fn()).filter(v=>v!==DROP)}
  if(value&&typeof value==='object'&&['step','section'].includes(value.type)&&typeof value.text==='string'&&Object.keys(value).every(k=>['type','text'].includes(k))){const text=visit(value.text,value.type==='section');return ()=>{const next=text();return next===DROP?DROP:{...value,text:next}}}
  if(value!=null)result.uncertain.push('Unsupported instruction structure retained without modification.');return ()=>value;
 };
 const rebuild=visit(meal.instructions);
 // Reuse the same proven website-section/image recognition for legacy instruction
 // lines, then apply the existing cooking-token, association and progress guards.
 const footer=recipeRepairLegacyNotes({...meal,notes:units.map(u=>u.line).join('\n')},library);
 for(const index of footer.removedIndices)if(!units[index].remove)units[index].remove='Confirmed RecipeSage footer/image clutter (instructions)';
 const linked=new Set((meal.linkedMealIds||[]).map(id=>library.find(m=>String(m.id)===String(id))).filter(Boolean).map(m=>recipeReferenceTitle(m.name)));
 for(let i=0;i<units.length;i++){
  const unit=units[i];if(unit.remove||!unit.text)continue;
  const isLinked=linked.has(recipeReferenceTitle(unit.text));if(unit.kind!=='section'&&!isLinked)continue;
  let end=i+1;while(end<units.length&&units[end].kind!=='section')end++;
  const body=units.slice(i+1,end).filter(u=>u.text),onlyMetadata=body.length>0&&body.every(u=>u.remove),families=new Set(body.map(u=>u.remove));
  if(isLinked&&!unit.links.length&&!/https?:\/\/|<a\b/i.test(unit.line)&&onlyMetadata&&families.has('account')&&families.has('timestamp'))unit.remove='stray linked heading';
  else if(isLinked||onlyMetadata)result.uncertain.push('Heading retained for review: '+unit.text+(isLinked?' (linked recipe; structure does not prove it is stray boilerplate).':'.'));
 }
 for(const unit of units){if(unit.remove)result.removed.push({text:unit.line,reason:unit.remove});else if(/(?:create (?:an? |your )?account|register\s*\/\s*login|^(?:created|last edited)\s*:?\s*\d)/i.test(unit.text))result.uncertain.push('Uncertain content retained: '+unit.line)}
 if(!result.removed.length)return result;
 let instructions=rebuild();if(instructions===DROP)instructions=typeof meal.instructions==='string'?'':[];
 const replacement={...meal,instructions},old=cookingItemTokens(meal),next=cookingItemTokens(replacement),oldTokens=new Set(old.steps.filter(s=>s.token).map(s=>s.token)),nextTokens=new Set(next.steps.filter(s=>s.token).map(s=>s.token));
 if(next.steps.some(s=>s.token&&!oldTokens.has(s.token))){result.reason='Cleanup would change retained cooking-step identity or section context; skipped for review.';return result}
 if(JSON.stringify(validRecipeIngredientLinks(meal))!==JSON.stringify(validRecipeIngredientLinks(replacement))){result.reason='Cleanup would change ingredient associations; skipped for review.';return result}
 if(Object.values(cookingSessions.occurrences).some(s=>s.context.mealId===String(meal.id)&&s.steps.some(token=>!nextTokens.has(token)))){result.reason='Cleanup would remove a step with saved progress; skipped for review.';return result}
 result.instructions=instructions;return result;
}
// Notes are displayed separately by the viewer; instruction cleanup cannot repair them.
function recipeRepairLegacyNotes(meal,library=meals){
 const result={notes:null,removed:[],uncertain:[],removedIndices:[]};
 const sage=recipeSageUuidPattern.test(String(meal.recipeSageId||''))||[meal.url,meal.originalRecipeUrl,meal.sourceUrl,meal.ingredientImportUrl].some(value=>{try{const u=new URL(value);return /^(?:www\.|android\.)?recipesage\.com$/i.test(u.hostname)&&recipeRepairIds(meal).some(id=>recipeSageUuidPattern.test(id))}catch(e){return false}});
 if(!sage||meal.notes==null||meal.notes==='')return result;
 if(typeof meal.notes!=='string'){result.uncertain.push('Unsupported notes structure retained without modification.');return result}
 const units=(meal.notes.match(/[^\r\n]*(?:\r\n|\r|\n|$)/g)||[]).filter(Boolean).map(raw=>{const line=raw.replace(/(?:\r\n|\r|\n)$/,''),plain=recipeRepairLegacyLine(line);return {raw,line,...plain,metadata:recipeRepairBoilerplate(plain.text,plain.links),remove:''}});
 // A pair of standalone account/date lines in the terminal footer is evidence;
 // a heading, a date, or an image by itself never justifies changing saved notes.
 let footer=units.length;while(footer>0&&(!units[footer-1].text||units[footer-1].metadata))footer--;
 const trailer=units.slice(footer),types=new Set(trailer.map(u=>u.metadata));
 if(!types.has('account')||!types.has('timestamp')){
  if(units.some(u=>u.metadata||/linked recipes|!\[/i.test(u.line)))result.uncertain.push('Notes retained: no confirmed terminal RecipeSage account-and-timestamp footer.');
  return result;
 }
 trailer.forEach(u=>{if(u.metadata)u.remove='RecipeSage '+u.metadata+' footer (notes)'});
 const related=unit=>!unit.links.length&&/^(?:linked|related) recipes:?$/i.test(unit.text);
 const genericAlt=alt=>/^(?:image|photo|picture)(?:\s+\d+)?$/i.test(alt.trim());
 const logoUrl=value=>{try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)&&/^(?:www\.)?recipesage\.com$/i.test(u.hostname)&&u.pathname==='/app/assets/imgs/logo_green_padded.png'&&!u.search&&!u.hash}catch(e){return false}};
 const image=unit=>{const md=unit.line.trim().match(/^!\[([^\]]*)\](?:\((<?[^\s)>]+>?)\))?$/);if(md&&genericAlt(md[1]))return md[2]?(logoUrl(md[2].replace(/^<|>$/g,''))?'logo':''):'placeholder';return ''};
 for(let i=footer-1;i>=0;i--){if(!units[i].text)continue;if(!image(units[i]))break;units[i].remove='RecipeSage footer image placeholder (notes)'}
 let marker=-1;for(let i=0;i<footer;i++)if(related(units[i]))marker=i;
 const titles=new Set(library.map(m=>recipeReferenceTitle(m.name))),savedLinks=new Set((meal.linkedMealIds||[]).map(id=>library.find(m=>String(m.id)===String(id))).filter(Boolean).map(m=>recipeReferenceTitle(m.name)));
 if(marker>=0){
  const body=units.slice(marker+1,footer),nonblank=body.filter(u=>u.text),hasLogo=nonblank.some(u=>image(u)==='logo');
  const plainTitles=new Set();let previous='';
  for(const u of nonblank){const img=image(u);if(img){previous=img;continue}if(previous==='logo'&&!u.links.length&&!/https?:\/\/|<a\b/i.test(u.line)&&titles.has(recipeReferenceTitle(u.text))&&!savedLinks.has(recipeReferenceTitle(u.text)))plainTitles.add(u);previous=''}
  const proven=hasLogo&&nonblank.every(u=>image(u)||plainTitles.has(u));
  // Never delete an actual linked-recipe URL, saved-link title, meaningful image,
  // unknown suggestion or surrounding user text. Preserve uncertain sections.
  if(proven){units[marker].remove='Confirmed RecipeSage related-section heading (notes)';for(const u of nonblank)u.remove=image(u)?'RecipeSage logo/image placeholder (notes)':'RecipeSage logo-associated suggestion heading (notes)'}
  else{
   for(const u of body)if(image(u))u.remove='RecipeSage footer image placeholder (notes)';
   result.uncertain.push('Related-recipe heading/content retained in notes: the section contains a saved link, URL, meaningful image or unconfirmed user content.');
  }
 }
 units.forEach((u,i)=>{if(u.remove){result.removed.push({text:u.line,reason:u.remove});result.removedIndices.push(i)}});
 const kept=units.filter(u=>!u.remove).map(u=>u.raw).join('');result.notes=kept.trim()?kept:'';return result;
}
function recipeRepairPlan(items,library=meals,allowWeb=false){
 const cleanups=library.map(meal=>recipeRepairLegacyCleanup(meal,library,allowWeb));
 const projected=library.map((meal,i)=>cleanups[i].instructions!==null?{...meal,instructions:cleanups[i].instructions}:meal);
 const missing=recipeMissingInstructionPlan(items,projected);
 const rows=missing.rows.map((row,i)=>{
  const cleanup=cleanups[i],restoring=row.instructions!==null;row={...row,meal:library[i],cleanup,uncertain:cleanup.uncertain,removedSaved:cleanup.removed};
  if(cleanup.reason){row.instructions=null;row.reason=cleanup.reason;row.kind='';return row}
  if(cleanup.instructions!==null){if(!restoring)row.instructions=cleanup.instructions;row.kind=restoring?'restore+cleanup':'cleanup';row.reason=restoring?'Restore missing instructions and remove confirmed legacy boilerplate.':'Remove confirmed legacy boilerplate only; retain cooking content.';row.method=restoring?row.method:'Recognized saved RecipeSage boilerplate; retained cooking tokens/associations verified.'}
  else row.kind=restoring?'restore':'';
  return row;
 });
 for(const row of rows){
  const notes=recipeRepairLegacyNotes(row.meal,library);row.notes=notes.notes;row.notesCleanup=notes;row.uncertain=[...row.uncertain,...notes.uncertain];
  if(row.notes!==null&&row.cleanup.reason){row.blockedSaved=row.removedSaved;row.removedSaved=[];row.uncertain.push('Instruction cleanup skipped; '+row.blockedSaved.length+' recognized instruction lines retained: '+row.cleanup.reason)}
  if(row.notes!==null){row.removedSaved=[...row.removedSaved,...notes.removed];if(!row.kind.includes('cleanup'))row.kind+=(row.kind?'+':'')+'cleanup';row.reason+=' Clean confirmed RecipeSage clutter from notes; preserve remaining notes verbatim.';row.method=(row.method?row.method+' ':'')+'Notes: RecipeSage provenance + terminal account/date footer; related headings require a confirmed logo-only website section.'}
 }
 const ready=rows.filter(r=>r.instructions!==null||r.notes!==null);
 return {rows,ready,matched:missing.matched,ambiguous:missing.ambiguous,restoring:ready.filter(r=>r.kind.includes('restore')).length,cleaning:ready.filter(r=>r.kind.includes('cleanup')).length,lines:ready.reduce((n,r)=>n+(r.kind.includes('cleanup')?r.removedSaved.length:0),0),uncertain:rows.filter(r=>r.uncertain.length||r.cleanup.reason).length,skippedLines:rows.reduce((n,r)=>n+(r.blockedSaved?.length||0)+(r.instructions===null&&r.notes===null?r.removedSaved.length:0),0)};
}
function recipeRepairPreviewText(value){return typeof value==='string'?value:Array.isArray(value)?value.map(block=>typeof block==='string'?block:block&&typeof block.text==='string'?(block.type==='section'?'## ':'')+block.text:JSON.stringify(block)).join('\n\n'):JSON.stringify(value??'',null,2)}

function openBackupRestorePicker(onError=error=>showAppMessage(error.message),canRestore=null){
 const input=document.createElement('input');input.type='file';input.accept='.json,application/json,*/*';
 input.onchange=async()=>{
  const file=input.files?.[0];if(!file)return;
  try{const backup=JSON.parse(await file.text());await restoreVersion2Backup(backup,canRestore)}
  catch(error){onError(error)}
 };
 input.click();
}
async function restoreVersion2Backup(backup,canRestore=null){
 const replacement=normalizeImportedBackup(backup);validateBackupStorage(replacement);
 const preparation=await prepareOptionalBackupPhotos(backup);if(preparation.cancelled)return;
 if(canRestore&&!canRestore())throw Error('Your library changed while the backup was being read. Nothing was restored.');
 const finish=()=>{restoreBackupStorage(replacement);recipePhotoNotice(preparation.warnings);mealPersistence.reload()};
 restoreBackupStorage(replacement,{id:'backup-restore',kind:'backup-restore',ownerId:null,retry:finish});
 recipePhotoNotice(preparation.warnings);mealPersistence.reload();
}
// Shared popup shell: the existing dialog owns focus, viewport and Android Back.
function recipeImportDialog(title){
 const origin={scroll:scrollY,planId:activePlanId,view:appViewSnapshot().view},d=recipeBulkDialog(title,null,true);d.overlay.classList.add('recipe-import-popup');
 const returned=new MutationObserver(()=>{if(d.overlay.isConnected)return;returned.disconnect();if(d.navigate)return;groupHistorySettled.then(()=>requestAnimationFrame(()=>requestAnimationFrame(()=>{if(!d.navigate&&activePlanId===origin.planId&&appViewSnapshot().view===origin.view&&editId===null)scrollTo({top:origin.scroll,behavior:'instant'})}))) });returned.observe(document.body,{childList:true});
 const heading=d.panel.firstElementChild;heading.className='recipe-import-heading';
 const text=document.createElement('span');text.textContent=title;heading.replaceChildren(text);
 const close=document.createElement('button');close.type='button';close.className='iconbtn';setIconButton(close,'cancel','Close '+title.toLowerCase());close.onclick=()=>d.close();heading.append(close);return d;
}
function recipeImportLikelySide(record){
 const tags=recipeImportTags(record).map(tag=>tag.toLowerCase().trim());
 if(tags.some(tag=>/^(?:side(?: dish)?s?|accompaniments?|vegetable sides?)$/.test(tag)))return true;
 if(tags.length)return false; // Explicit metadata is stronger than a name guess.
 return /^(?:(?:easy|simple|crispy|garlic|herbed|buttery)\s+)*(?:roasted|steamed|mashed|sauteed|sautéed)\s+(?:potatoes|carrots|broccoli|asparagus|vegetables)\b/i.test(record.name||'');
}
async function reviewRecipeImportItems(items,filename){
 if(items.length!==1||meals.some(m=>m.importSourceId===recipeImportIdentity(items[0]))){showRecipeImportSelection(items,filename);return}
 const raw=items[0],details=completeRecipeFields(raw),sourceId=recipeImportIdentity(raw);
 const record={...details,name:details.name||raw.name||'Imported recipe',labels:recipeImportTags(raw),...recipeImportStatus(raw,false),groceryDefaultAll:true,url:recipeImportUrl(raw),sourceUrl:recipeImportSourceUrl(raw),importSourceId:sourceId,recipeSageId:recipeSageUuidPattern.test(sourceId)?sourceId:'',recipeImportPending:false};
 if(raw.aiStepTags){const links=askAiStepLinks(record,raw.aiStepTags);if(links)record.ingredientStepLinks=links}
 if(raw.aiReplacesRecipeId){record.aiReplacesRecipeId=raw.aiReplacesRecipeId;record.aiReplaceMode=raw.aiReplaceMode==='replace'?'replace':'update'}if(raw.aiReturnToGroups)record.aiReturnToGroups=true;
 // Creation, membership changes, Save, Cancel and Undo all use the ordinary editor.
 await navigateAfterSettings(()=>addRecipeToGroup(raw.aiTargetGroup&&cats.includes(raw.aiTargetGroup)?raw.aiTargetGroup:'',record));
 if(editId!==null){const missing=[];if(!record.ingredients?.length)missing.push('ingredients');if(!record.prep&&!record.cook&&!record.total)missing.push('cooking times');if(missing.length){const note=document.createElement('p');note.className='muted import-missing-fields';note.textContent='The source did not provide readable '+missing.join(' or ')+'. Review and add them before saving.';document.querySelector('#editor .meal-editor-fields')?.prepend(note)}}
 if(editId!==null){const recipe=document.querySelector('[data-editor-section=recipe]');if(recipe)recipe.open=true}
}
function openRecipeImportFilePicker(){openRecipeImportSourcePicker('file')}
function openRecipeImportTrelloLink(){openRecipeImportSourcePicker('trello')}
function openRecipeImportSourcePicker(initial='website'){
 const d=recipeImportDialog('Import recipes'),methods=document.createElement('fieldset'),legend=document.createElement('legend');legend.textContent='Import from';methods.className='recipe-import-methods';methods.append(legend);
 const body=document.createElement('div');body.className='recipe-import-method-body';const status=document.createElement('p');status.className='muted';status.setAttribute('role','status');
 const actions=document.createElement('div');actions.className='meal-unified-actions';const review=document.createElement('button');review.type='button';review.className='smallbtn recipe-review-action';review.textContent='Review recipe';actions.append(review);
 let method=initial,controller=null,generation=0,selectedPhoto=null;
 const originalClose=d.close;d.close=(...args)=>{generation++;controller?.abort();originalClose(...args)};
 // The shell's Back/X/Escape can remove it directly; invalidate all pending work too.
 const watch=new MutationObserver(()=>{if(!d.overlay.isConnected){generation++;controller?.abort();watch.disconnect()}});watch.observe(document.body,{childList:true});
 const fields={};
 function field(label,element){const wrap=document.createElement('label');wrap.className='recipe-import-field';const text=document.createElement('span');text.textContent=label;element.setAttribute('aria-label',label);wrap.append(text,element);body.append(wrap);return element}
 function hint(text){const p=document.createElement('p');p.className='muted';p.textContent=text;body.append(p)}
 function show(next){
  generation++;controller?.abort();method=next;body.replaceChildren();status.textContent='';review.disabled=false;selectedPhoto=null;
  review.textContent=next==='file'?'Read recipe file':next==='trello'?'Read board':'Review recipe';
  if(next==='website'){fields.url=field('Website link',document.createElement('input'));fields.url.type='url';fields.url.placeholder='https://…'}
  if(next==='text'){fields.text=field('Recipe text',document.createElement('textarea'));fields.text.rows=8;fields.text.placeholder='Title: Recipe name\nIngredients\n1 cup rice\nInstructions\nCook the rice.'}
  if(next==='photo'){
   hint('Choose a clear recipe photo. Recognized text is editable before review.');fields.text=field('Recognized recipe text',document.createElement('textarea'));fields.text.rows=6;
   for(const [label,camera]of [['Choose photo',false],['Use camera',true]]){const input=document.createElement('input');input.type='file';input.accept='image/*';if(camera)input.capture='environment';input.hidden=true;const button=document.createElement('button');button.type='button';button.className='smallbtn';button.textContent=label;button.onclick=()=>input.click();body.append(button,input);input.onchange=()=>{selectedPhoto=input.files?.[0]||null;if(selectedPhoto)readPhoto()}}
  }
  if(next==='file'){hint('Supported exports: RecipeSage, Paprika, Mela, Trello, CSV, JSON / JSON-LD, HTML and ZIP.');fields.file=field('Recipe file',document.createElement('input'));fields.file.type='file';fields.file.accept='.jsonld,.json,.csv,.html,.htm,.zip,.paprikarecipes,.melarecipe,.melarecipes,.paprikarecipe,application/json,text/csv,application/zip,*/*'}
  if(next==='trello'){fields.board=field('Trello board link',document.createElement('input'));fields.board.type='url';fields.board.placeholder='https://trello.com/b/…';hint('Public boards may be readable directly. For private or blocked boards, select Recipe file and use Trello’s JSON export.')}
 }
 async function readPhoto(){const current=++generation;controller?.abort();controller=new AbortController();review.disabled=true;status.textContent='Reading photo…';try{if(await ingredientPhotoIsBlank(selectedPhoto))throw Error('No readable text found. Choose a clearer photo.');const text=await recognizeIngredientPhoto(selectedPhoto,controller.signal);if(current!==generation||!d.overlay.isConnected)return;fields.text.value=text;status.textContent='Check the recognized text, then review your recipe.'}catch(e){if(current===generation&&d.overlay.isConnected)status.textContent=e.message}finally{if(current===generation)review.disabled=false}}
 for(const [value,label]of [['website','Website link'],['photo','Photo or camera'],['text','Paste text'],['file','Recipe file'],['trello','Trello board link']]){const row=document.createElement('label'),radio=document.createElement('input');radio.type='radio';radio.name='recipeImportMethod';radio.value=value;radio.checked=value===initial;radio.onchange=()=>{if(radio.checked)show(value)};row.append(radio,document.createTextNode(label));methods.append(row)}
 review.onclick=async()=>{
  const current=++generation;controller?.abort();controller=new AbortController();review.disabled=true;status.textContent='Reading recipe…';
  try{
   let items=[],filename='import';
   if(method==='file'){const file=fields.file.files?.[0];if(!file)throw Error('Choose a recipe file.');items=await recipeImportReadFile(file);filename=file.name}
   else if(method==='trello'){let url;try{url=new URL(fields.board.value.trim())}catch(_){throw Error('Enter a complete Trello board URL.')};if(url.protocol!=='https:'||!['trello.com','www.trello.com'].includes(url.hostname)||!/^\/b\/[a-z0-9]{6,}/i.test(url.pathname))throw Error('Enter a link beginning with https://trello.com/b/');const response=await fetch('https://trello.com/b/'+encodeURIComponent(url.pathname.split('/')[2])+'.json',{credentials:'omit',signal:controller.signal});if(!response.ok)throw Error('Trello blocked access. Export the board as JSON and use Recipe file.');items=recipeImportItems(await response.json());filename='Trello board'}
   else if(method==='website'){const lines=await importIngredientsFromWebsite(fields.url.value.trim(),controller.signal);const details=lines.recipeDetails||{};items=[{...details,ingredients:lines.length?[...lines]:(details.ingredients||[]),name:details.name||'Imported recipe',url:fields.url.value.trim()}]}
   else{const text=fields.text.value.trim();if(!text)throw Error('Enter recipe text first.');const details=extractCompleteRecipe(text)||recipeTextSections(text);if(!details.ingredients?.length&&!details.instructions?.some(step=>step.type==='step'))details.notes=details.notes||text;items=[{...details,name:details.name||text.split(/\r?\n/)[0].replace(/^Title:\s*/i,'').trim()||'Imported recipe',ingredients:details.ingredients||extractRecipeIngredients(text)}]}
   if(current!==generation||!d.overlay.isConnected)return;if(!items.length)throw Error('No recipes were found. Check the selected source.');d.navigate=true;d.close();await groupHistorySettled;await editorHistorySettled;await reviewRecipeImportItems(items,filename);
  }catch(e){if(current===generation&&d.overlay.isConnected)status.textContent=e.message||'Import could not be read. No recipes changed.'}finally{if(current===generation)review.disabled=false}
 };
 d.panel.append(methods,body,status,actions);show(initial);
}

// Ask AI (2026-11-19, copy-and-paste version): builds a request from Family tastes, favorites and Regulars,
// opens Claude or copies it, then reads the pasted answer through the normal import review (Off menu).
const FAMILY_TASTES_KEY='mealRotationFamilyTastesV1';
let familyTastes=(()=>{try{const v=JSON.parse(localStorage.getItem(FAMILY_TASTES_KEY)||'null'),text=k=>typeof v?.[k]==='string'?v[k]:'';const links={};if(v&&typeof v.links==='object'&&v.links&&!Array.isArray(v.links))for(const [k,x] of Object.entries(v.links))if(typeof x==='string')links[k]=x;return {likes:text('likes'),restrictions:text('restrictions'),claudeLink:text('claudeLink'),links}}catch(e){return {likes:'',restrictions:'',claudeLink:'',links:{}}}})();
function saveFamilyTastes(next=familyTastes){const links={};for(const [k,x] of Object.entries(next.links||{}))if(typeof x==='string'&&x.trim())links[k]=x;familyTastes={likes:String(next.likes||''),restrictions:String(next.restrictions||''),claudeLink:String(next.claudeLink||''),links};try{if(familyTastes.likes.trim()||familyTastes.restrictions.trim()||familyTastes.claudeLink.trim()||Object.keys(links).length)localStorage.setItem(FAMILY_TASTES_KEY,JSON.stringify(familyTastes));else localStorage.removeItem(FAMILY_TASTES_KEY)}catch(e){}}
const AI_RESTRICTION_WORDS={
 dairy:{words:['milk','butter','cream','cheese','yogurt','yoghurt','ghee','whey','casein','buttermilk','parmesan','mozzarella','cheddar','ricotta','feta','half-and-half','creme fraiche','crème fraîche','lactose'],ok:['coconut milk','coconut cream','oat milk','almond milk','soy milk','rice milk','cashew milk','peanut butter','almond butter','cashew butter','sunflower butter','nut butter','apple butter','vegan butter','dairy-free','dairy free','non-dairy','cream of tartar','butternut','butter lettuce','butter beans','coconut yogurt']},
 soy:{words:['soy','soya','tamari','miso','hoisin','oyster sauce','edamame','tofu','tempeh','shoyu','teriyaki','ponzu','black bean sauce','doubanjiang','gochujang','kecap manis','natto'],ok:['soy-free','soy free','coconut aminos']},
 gluten:{words:['flour','wheat','bread','breadcrumbs','panko','pasta','spaghetti','barley','rye','couscous','seitan','beer','soy sauce','hoisin','udon','ramen','orzo','croutons','tortilla'],ok:['gluten-free','gluten free','rice flour','almond flour','coconut flour','tapioca flour','cassava flour','corn tortilla','rice noodles','rice paper','cornstarch','corn starch','buckwheat']},
 nuts:{words:['peanut','peanuts','almond','almonds','cashew','cashews','walnut','walnuts','pecan','pecans','pistachio','pistachios','hazelnut','hazelnuts','macadamia','pine nut','pine nuts','nut butter'],ok:['nut-free','nut free','coconut','nutmeg','water chestnut','butternut']},
 eggs:{words:['egg','eggs','yolk','yolks','mayonnaise','mayo','meringue'],ok:['eggplant','egg-free','egg free','vegan mayo']},
 shellfish:{words:['shrimp','prawn','prawns','crab','lobster','scallop','scallops','clam','clams','mussel','mussels','oyster','oysters','crawfish','crayfish','oyster sauce'],ok:[]},
 pork:{words:['pork','bacon','ham','prosciutto','pancetta','lard','chorizo','salami','pepperoni','guanciale'],ok:['hamburger']}
};
function familyRestrictionRules(text=familyTastes.restrictions){
 const rules=[],seen=new Set();
 for(let part of String(text||'').toLowerCase().split(/[,;\n]|\band\b|\bor\b/)){part=part.replace(/\b(?:no|without|avoid|free|allergic|allergy|to|of|any)\b/g,' ').replace(/-free\b/g,' ').replace(/[.!]/g,' ').replace(/\s+/g,' ').trim();if(!part)continue;
  const key=/dairy|lactose|milk/.test(part)?'dairy':/\bsoy/.test(part)?'soy':/gluten|wheat|celiac/.test(part)?'gluten':/\bnut|peanut/.test(part)?'nuts':/\beggs?\b/.test(part)?'eggs':/shellfish|shrimp/.test(part)?'shellfish':/\bpork\b/.test(part)?'pork':null;
  const id=key||part;if(seen.has(id))continue;seen.add(id);rules.push(key?{label:key==='nuts'?'nuts':key,...AI_RESTRICTION_WORDS[key]}:{label:part,words:[part],ok:[]});
 }return rules;
}
function restrictionConflicts(lines,rules=familyRestrictionRules()){
 const found=[];const escape=w=>w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 for(const raw of lines||[]){const line=String(typeof raw==='string'?raw:raw?.text||'');let text=' '+line.toLowerCase()+' ';
  for(const rule of rules){let t=text;for(const ok of rule.ok)t=t.split(ok).join(' ');if(rule.words.some(w=>new RegExp('(^|[^a-z])'+escape(w)+'(?:e?s)?(?![a-z])').test(t))){found.push({line:line.trim(),label:rule.label});break}}
 }return found;
}
function recipeMainIngredients(meal,limit=8){
 const lines=(meal.ingredients||[]).map(i=>String(typeof i==='string'?i:i?.text||'')).filter(l=>l.trim()&&!/^[A-Z\s&]+:?$/.test(l.trim()));
 return lines.slice(0,limit).map(l=>l.replace(/\([^)]*\)/g,'').replace(/^[\d\s\/½⅓⅔¼¾⅛.,-]+/,'').replace(/^(?:cups?|tbsp|tablespoons?|tsp|teaspoons?|lbs?|pounds?|oz|ounces?|g|grams?|kg|ml|cloves?|cans?|large|medium|small|bunch)\b\.?\s*/i,'').replace(/^of\s+/i,'').split(',')[0].trim()).filter(Boolean);
}
// Ask AI page (2026-11-19): one request builder for every job. The profile (tastes, restrictions,
// favorites, Regulars) goes with ideas and recipe jobs; recipes from the app are sent as plain text.
function aiProfileLines(options={}){
 const seen=new Set(),unique=list=>list.filter(m=>{const k=String(m.name||'').trim().toLowerCase();if(!k||seen.has(k))return false;seen.add(k);return true});
 const usable=meals.filter(m=>!m._scheduledEditorDraft&&!m.temporaryMeal&&m.name);
 const favorites=unique(usable.filter(m=>m.favorite===true)).slice(0,20),regulars=unique(usable.filter(m=>recipeStatus(m)==='rotation')).slice(0,60),out=[];
 if(familyTastes.likes.trim())out.push('Our tastes: '+familyTastes.likes.trim());
 if(familyTastes.restrictions.trim())out.push(options.strict?'Our restrictions: '+familyTastes.restrictions.trim()+'. Follow them, including hidden sources in sauces, broths and seasonings.':'Our usual restrictions: '+familyTastes.restrictions.trim()+'. Follow them, including hidden sources in sauces, broths and seasonings. But if my request asks for something that conflicts with them, don\'t assume: first ask me whether to keep it as asked (I may be cooking for someone else) or use substitutes.');
 if(favorites.length){out.push('','Our family favorites, the meals we love most (main ingredients in parentheses):');for(const m of favorites){const main=recipeMainIngredients(m);out.push('- '+m.name+(main.length?' ('+main.join(', ')+')':''))}}
 if(regulars.length&&!options.noRegulars)out.push('','Other meals we already cook'+(options.avoidRepeats?' (for style only; please don\'t suggest these)':'')+': '+regulars.map(m=>m.name).join('; '));
 return out;
}
const AI_RECIPE_FORMAT=['Title: Recipe name','Prep time: 15 minutes','Cook time: 30 minutes','Servings: 4','Ingredients','1 lb chicken thighs [2]','3 cloves garlic, minced [3, 5]','...','Instructions','1. First step.','...','Notes','Any tips (optional).'];
const AI_TAG_RULE='Important: end EVERY ingredient line with the number(s) of the instruction steps that use it, in square brackets, like [2] or [3, 5]. Section labels (like "For the sauce:") get no brackets.';
function aiRecipeText(meal){
 const lines=['Recipe: '+(meal.name||'Untitled'),'Ingredients:'];for(const l of meal.ingredients||[]){const t=String(typeof l==='string'?l:l?.text||'').trim();if(t)lines.push(t)}
 const steps=(meal.instructions||[]).map(x=>typeof x==='string'?{type:'step',text:x}:x).filter(x=>x&&String(x.text||'').trim());if(steps.length){lines.push('Instructions:');let n=0;for(const x of steps)lines.push(x.type==='section'?String(x.text):(++n)+'. '+x.text)}
 return lines.join('\n');
}
function buildAiJobRequest(job,data={}){
 const out=[],source=data.recipe?aiRecipeText(data.recipe):String(data.source||'').trim(),format=()=>out.push('',...AI_RECIPE_FORMAT);
 if(job==='fridge'){out.push('Help me plan a dinner for my family using what I have.','','What I have: '+String(data.input||'').trim(),'',...aiProfileLines({avoidRepeats:true}),'','This is a two-step conversation.','','Step 1 (your reply now): suggest 3 different meals that mainly use what I have (pantry staples are fine). For each, give only a number, the name and one line on why it fits us. Then stop and ask which ones I want. Do NOT write any full recipe yet.','','Step 2 (after I answer with a number, several numbers, or "all"): write each recipe I chose in exactly the format below, one after another, with nothing before or after. '+AI_TAG_RULE);format()}
 else if(job==='write'){out.push('I\'d like a recipe for my family: '+String(data.input||'').trim(),'',...aiProfileLines({avoidRepeats:true}),'','This is a two-step conversation.','','Step 1 (your reply now): suggest 3 different recipes that fit what I asked. For each, give only a number, the name and one line on why it fits us. Then stop and ask which ones I want. Do NOT write any full recipe yet.','','Step 2 (after I answer with a number, several numbers, or "all"): write each recipe I chose in exactly the format below, one after another, with nothing before or after. '+AI_TAG_RULE);format()}
 else if(job==='convert'){out.push('Convert this recipe so it follows our restrictions and suits our tastes. Keep it as close to the original as you can.'+(String(data.extra||'').trim()?' Also: '+String(data.extra).trim():''),'',source,'',...aiProfileLines({strict:true,noRegulars:true}),'','First list what you changed in a few short lines. Then give the full converted recipe in exactly this format. '+AI_TAG_RULE);format()}
 else if(job==='like'){out.push('Would my family like this recipe? Give an honest verdict in a few sentences, based on our tastes, restrictions and favorites below.','',source,'',...aiProfileLines({strict:true}),'','If tweaks would make it a better fit, say what they are. Then give the recipe, with your suggested tweaks, in exactly this format so I can save it. '+AI_TAG_RULE);format()}
 else if(job==='out'){out.push('I\'m cooking this right now and I\'m out of '+String(data.missing||'an ingredient').trim()+'. What\'s the best substitute I\'m likely to have at home, and how much should I use? Keep it short.','',source);if(familyTastes.restrictions.trim())out.push('','Our restrictions: '+familyTastes.restrictions.trim()+'.')}
 return out.join('\n');
}
function buildAskAiRequest(mode,input){return buildAiJobRequest(mode==='fridge'?'fridge':'write',{input})}
function askAiDurationMinutes(text){const t=String(text||'').toLowerCase();let total=0,found=false;const h=t.match(/(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours)\b/),m=t.match(/(\d+)\s*(?:m|min|mins|minute|minutes)\b/);if(h){total+=Math.round(parseFloat(h[1])*60);found=true}if(m){total+=parseInt(m[1],10);found=true}if(!found){const n=t.match(/^\s*(\d+)\s*$/);if(n){total=parseInt(n[1],10);found=true}}return found&&total>0?total:null}
function askAiItemFromAnswer(answer){
 let text=String(answer||'').replace(/\r/g,'').replace(/^```[a-z]*\n?|```$/gm,'').trim();const start=text.search(/^\s*(?:\*\*)?Title:/im);if(start>0)text=text.slice(start);
 text=text.replace(/(?:\n[ \t]*(?:enjoy|hope (?:this|that|you)|let me know|feel free|happy cooking|bon app|i can also|would you like|want me to)[^\n]*)+\s*$/i,'').trim();
 if(!text)throw Error('Paste the AI\'s answer first.');
 const details=extractCompleteRecipe(text)||recipeTextSections(text);if(!details.ingredients?.length&&!details.instructions?.some(step=>step.type==='step'))details.notes=details.notes||text;
 const field=name=>(text.match(new RegExp('^\\s*(?:\\*\\*)?'+name+'(?:\\*\\*)?\\s*:\\s*(?:\\*\\*)?\\s*(.+)$','im'))||[])[1]||'';
 // The requested format has an "Ingredients" heading; read that block directly (generic extraction can take steps).
 const block=[],stepTags={},lines=text.split('\n');let inside=false;for(const line of lines){const head=line.trim().replace(/^#{1,6}\s*/,'').replace(/\*\*/g,'').replace(/:$/,'').trim();if(/^ingredients$/i.test(head)){inside=true;continue}if(inside&&/^(?:instructions|directions|method|steps|notes)$/i.test(head))break;if(inside&&line.trim()){const clean=line.trim().replace(/^(?:[-*•]|\d+[.)])\s+/,''),tag=clean.match(/\s*\[\s*(?:steps?\s*)?(\d+(?:\s*(?:,|&|and)\s*\d+)*)\s*\]\s*$/i),text=tag?clean.slice(0,tag.index).trim():clean;block.push(text);if(tag)stepTags[ingredientLine(text)]=tag[1].split(/\s*(?:,|&|and)\s*/).map(Number)}}
 const item={...details,name:(details.name||field('Title')||text.split('\n')[0]).replace(/\*\*/g,'').replace(/^["“”‘’'\s]+|["“”‘’'\s]+$/g,'').trim()||'AI recipe',ingredients:block.length?block:details.ingredients?.length?details.ingredients:extractRecipeIngredients(text)};
 const prep=askAiDurationMinutes(field('Prep time')),cook=askAiDurationMinutes(field('Cook time'));if(prep&&!item.prep)item.prep=prep;if(cook&&!item.cook)item.cook=cook;if(Object.keys(stepTags).length)item.aiStepTags=stepTags;
 // Its own identity, so a repeat paste always opens the single-recipe review (not the bulk file importer).
 item.importSourceId='ask-ai:'+Date.now().toString(36)+Math.random().toString(36).slice(2,6);
 if(!item.ingredients?.length)throw Error('No ingredients were found. Paste the full recipe (Title, Ingredients, Instructions).');
 return item;
}
// Ask AI step tags -> saved step links (same as links set with the step chips). Every step gets an entry so
// the tags fully decide; untagged recipes keep automatic matching. Called by the import review.
function askAiStepLinks(record,tags){
 const items=recipeAssociationItems(record),byLine=new Map(items.ingredients.map(i=>[ingredientLine(i.text),i.token])),steps=items.steps,links=steps.map(s=>({step:s.token,ingredients:[]}));
 for(const [line,numbers]of Object.entries(tags||{})){const token=byLine.get(line);if(!token)continue;for(const n of numbers)if(links[n-1]&&!links[n-1].ingredients.includes(token))links[n-1].ingredients.push(token)}
 return links.some(l=>l.ingredients.length)?validRecipeIngredientLinks(record,links):undefined;
}
async function copyAskAiText(text){try{await navigator.clipboard.writeText(text);return true}catch(e){const area=document.createElement('textarea');area.value=text;area.style.cssText='position:fixed;opacity:0;top:0;left:0';document.body.append(area);area.select();let ok=false;try{ok=document.execCommand('copy')}catch(_){}area.remove();return ok}}
const AI_PENDING_KEY='mealRotationAskAiPendingV1';
const AI_JOBS={fridge:'What’s in my fridge',write:'Write a recipe',convert:'Change a recipe',like:'Would my family like it?',out:'Out of an ingredient'};
function aiPending(){try{const v=JSON.parse(localStorage.getItem(AI_PENDING_KEY)||'null');return v&&AI_JOBS[v.job]?v:null}catch(e){return null}}
function setAiPending(value){try{if(value)localStorage.setItem(AI_PENDING_KEY,JSON.stringify(value));else localStorage.removeItem(AI_PENDING_KEY)}catch(e){}}
function aiFindRecipe(id){return id==null?null:meals.find(m=>String(m.id)===String(id)&&!m._scheduledEditorDraft)||null}
// Which AI the Ask AI flow opens (2026-11-23): Claude by default. The request is ALWAYS copied first; links that
// prefill the question are used only when short enough, otherwise the AI's site opens and the person pastes.
const AI_TARGET_KEY='mealRotationAiTargetV1';
const AI_TARGETS={claude:{name:'Claude',url:t=>'https://claude.ai/new?q='+encodeURIComponent(t),home:'https://claude.ai/new'},chatgpt:{name:'ChatGPT',url:null,home:'https://chatgpt.com/'},copilot:{name:'Copilot',url:t=>'https://copilot.microsoft.com/?q='+encodeURIComponent(t),home:'https://copilot.microsoft.com/'},perplexity:{name:'Perplexity',url:t=>'https://www.perplexity.ai/search?q='+encodeURIComponent(t),home:'https://www.perplexity.ai/'},gemini:{name:'Gemini',url:null,home:'https://gemini.google.com/app'},copy:{name:'your AI',url:null,home:null}};
function aiTargetKey(){try{const v=localStorage.getItem(AI_TARGET_KEY);return AI_TARGETS[v]?v:'claude'}catch(e){return 'claude'}}
function aiTargetName(){return AI_TARGETS[aiTargetKey()].name}
// Short self-removing message (used after sending an Ask AI request, since the dialog closes right away).
function aiToast(message){
 if(!message)return;document.getElementById('aiToast')?.remove();const t=document.createElement('div');t.id='aiToast';t.setAttribute('role','status');t.setAttribute('aria-live','polite');t.textContent=message;
 t.style.cssText='position:fixed;left:50%;transform:translateX(-50%);bottom:calc(96px + env(safe-area-inset-bottom,0px));max-width:min(92vw,420px);background:#2f3a48;color:#fff;padding:11px 16px;border-radius:12px;font-size:15px;line-height:1.35;z-index:36000;box-shadow:0 6px 20px #0004;text-align:center';
 document.body.append(t);setTimeout(()=>t.remove(),6000);
}
// Send: copy the request, then open the chosen AI (Claude: the saved project/chat link, or a new prefilled chat).
async function sendAiRequest(text){
 const key=aiTargetKey(),target=AI_TARGETS[key],copied=await copyAskAiText(text),link=String((key==='claude'?familyTastes.claudeLink:familyTastes.links?.[key])||'').trim();
 if(key==='copy')return copied?'Request copied. Paste it into your AI.':'Could not copy the request.';
 if(/^https:\/\/\S+$/i.test(link)){window.open(link,'_blank','noopener');return copied?'Request copied. Paste it into '+target.name+'.':'Could not copy the request.'}
 const prefilled=target.url?target.url(text):'';
 if(prefilled&&(key==='claude'||prefilled.length<=1800)){window.open(prefilled,'_blank','noopener');return key==='claude'?'':copied?'Request copied. If it is not filled in, paste it.':''}
 window.open(target.home,'_blank','noopener');return copied?'Request copied. Paste it into '+target.name+'.':'Could not copy the request.';
}
// Recipe chooser used by Convert / Would they like it / Out of an ingredient (search by name, Regulars first).
function aiRecipePicker(onChange){
 const box=document.createElement('div');box.className='ai-recipe-picker';const input=document.createElement('input');input.type='search';input.placeholder='Search your recipes';input.setAttribute('aria-label','Search your recipes');const results=document.createElement('div');results.className='ai-recipe-results';box.append(input,results);
 const draw=()=>{results.replaceChildren();const q=input.value.trim().toLowerCase();if(!q)return;const seen=new Set();
  const found=meals.filter(m=>m.name&&!m._scheduledEditorDraft&&!m.temporaryMeal&&m.name.toLowerCase().includes(q)).sort((a,b)=>(recipeStatus(b)==='rotation')-(recipeStatus(a)==='rotation')||a.name.localeCompare(b.name)).filter(m=>{const k=sharedRecipeIdentity(m);if(seen.has(k))return false;seen.add(k);return true}).slice(0,6);
  if(!found.length){const none=document.createElement('p');none.className='muted ai-recipe-none';none.textContent='No recipes match.';results.append(none);return}
  for(const m of found){const b=document.createElement('button');b.type='button';b.className='ai-recipe-result';b.textContent=m.name;b.onclick=()=>onChange(m);results.append(b)}};
 input.oninput=draw;return {box,focus:()=>input.focus({preventScroll:true})};
}
function openAiJobDialog(job,recipe=null){
 const d=recipeImportDialog(recipe?AI_JOBS[job].replace(' a recipe','')+': '+recipe.name:AI_JOBS[job]);d.panel.classList.add('ask-ai-dialog');d.panel.dataset.aiJob=job;
 if(recipe)d.panel.querySelector('h3,h2,strong')?.classList.add('ai-dialog-title');
 const fromRecipe=!!recipe,needsSource=['convert','like','out'].includes(job);let chosen=recipe,sourceMode='mine';
 const body=document.createElement('div');body.className='ai-job-body';
 const input=document.createElement('textarea');input.className='ask-ai-input';input.rows=3;
 const sourceTabs=document.createElement('div');sourceTabs.className='serving-add-modes ask-ai-modes';sourceTabs.setAttribute('role','tablist');
 const chosenRow=document.createElement('div');chosenRow.className='ai-chosen-recipe';
 const sourceText=document.createElement('textarea');sourceText.className='ask-ai-input';sourceText.rows=4;sourceText.placeholder='Paste a recipe link or the recipe text';sourceText.setAttribute('aria-label','Recipe link or text');
 const extra=document.createElement('input');extra.type='text';extra.className='ai-extra';extra.placeholder='What should change? e.g. less spicy, quicker, no dairy';extra.setAttribute('aria-label','What should change');extra.setAttribute('aria-describedby','aiExtraHint');
 const missing=document.createElement('input');missing.type='text';missing.className='ai-extra';missing.placeholder='What are you out of?';missing.setAttribute('aria-label','What are you out of?');
 const chips=document.createElement('div');chips.className='ai-ingredient-chips';
 const picker=aiRecipePicker(m=>{chosen=m;draw()});
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');
 const status=document.createElement('p');status.className='muted ask-ai-status';status.setAttribute('role','status');
 const actions=document.createElement('div');actions.className='ai-send-actions';const open=document.createElement('button'),copy=document.createElement('button');open.type=copy.type='button';open.className='smallbtn ai-primary';open.textContent='Open in '+aiTargetName();copy.className='smallbtn';copy.textContent='Copy request';actions.append(...(aiTargetKey()==='copy'?[copy]:[open,copy]));
 function draw(){
  body.replaceChildren();error.textContent='';
  if(job==='fridge'||job==='write'){input.placeholder=job==='fridge'?'What do you have? e.g. chicken thighs, bok choy, rice, limes':'What would you like? e.g. crispy pork, quick weeknight';input.setAttribute('aria-label',AI_JOBS[job]);body.append(input);return}
  if(!fromRecipe&&job!=='out'){sourceTabs.replaceChildren();for(const [value,label]of [['mine','My recipe'],['found','Link or text']]){const tab=document.createElement('button');tab.type='button';tab.setAttribute('role','tab');tab.setAttribute('aria-selected',String(sourceMode===value));tab.textContent=label;tab.onclick=()=>{sourceMode=value;draw()};sourceTabs.append(tab)}body.append(sourceTabs)}
  if(sourceMode==='found'&&!fromRecipe&&job!=='out')body.append(sourceText);
  else if(chosen){chosenRow.replaceChildren();const name=document.createElement('strong');name.textContent=chosen.name;chosenRow.append(name);if(!fromRecipe){const change=document.createElement('button');change.type='button';change.className='ai-change-recipe';change.textContent='Change';change.onclick=()=>{chosen=null;draw();picker.focus()};chosenRow.append(change)}if(!fromRecipe)body.append(chosenRow)}
  else body.append(picker.box);
  if(job==='convert'){const hint=document.createElement('div');hint.id='aiExtraHint';hint.className='ai-extra-hint';hint.textContent='Leave blank to match your family’s restrictions and tastes.';body.append(extra,hint)}
  if(job==='out'&&chosen){body.append(missing);chips.replaceChildren();for(const line of (chosen.ingredients||[]).map(l=>String(typeof l==='string'?l:l?.text||'').trim()).filter(l=>l&&!/:\s*$/.test(l)).slice(0,14)){const chip=document.createElement('button');chip.type='button';chip.className='ai-ingredient-chip';chip.textContent=line;chip.onclick=()=>{missing.value=line;chips.querySelectorAll('.ai-ingredient-chip').forEach(c=>c.setAttribute('aria-pressed',String(c===chip)))};chip.setAttribute('aria-pressed','false');chips.append(chip)}body.append(chips)}
 }
 const request=()=>{
  if(job==='fridge'||job==='write'){if(!input.value.trim())throw Error(job==='fridge'?'List what you have first.':'Describe the recipe first.');return buildAiJobRequest(job,{input:input.value})}
  if(sourceMode==='found'&&!fromRecipe&&job!=='out'){if(!sourceText.value.trim())throw Error('Paste a recipe link or text first.');return buildAiJobRequest(job,{source:sourceText.value,extra:extra.value})}
  if(!chosen)throw Error('Choose a recipe first.');if(job==='out'&&!missing.value.trim())throw Error('Say what you’re out of first.');
  return buildAiJobRequest(job,{recipe:chosen,extra:extra.value,missing:missing.value});
 };
 const send=async viaLink=>{error.textContent='';let text;try{text=request()}catch(e){error.textContent=e.message;return}
  if(job!=='out')setAiPending({job,recipeId:chosen&&!(sourceMode==='found'&&!fromRecipe)?String(chosen.id):null,recipeName:chosen&&!(sourceMode==='found'&&!fromRecipe)?chosen.name:'',at:Date.now()});
  let ok=true,note='';if(viaLink)note=await sendAiRequest(text);else ok=await copyAskAiText(text);
  if(!ok){status.textContent='Could not copy the request.';return}
  // Close once sent, so coming back shows the page with its waiting-answer card.
  d.navigate=true;d.close();aiToast(note);
  // Started from a recipe page: go to Ask AI so the waiting-answer card is there when you come back.
  if(job!=='out'&&fromRecipe)setTimeout(()=>{if(recipeViewer)closeRecipeViewer();showTop=true;groceryTabActive=false;allMealsActive=false;aiTabActive=true;editId=null;render();window.scrollTo(0,0)},0);
  else if(job!=='out'&&aiTabActive)setTimeout(()=>renderList({readOnly:true}),0);
 };
 open.onclick=()=>send(true);copy.onclick=()=>send(false);for(const field of [input,sourceText,extra,missing])field.addEventListener('input',()=>{error.textContent=''});
 draw();d.panel.append(body,error,status,actions);setTimeout(()=>(job==='fridge'||job==='write'?input:fromRecipe?(job==='out'?missing:extra):picker).focus?.({preventScroll:true}),60);
 return d;
}
function openAskAiDialog(){openAiJobDialog('fridge')}
// From a recipe page: the three recipe jobs, with the recipe already chosen.
function openAiRecipeMenu(recipe){
 const d=recipeImportDialog('Ask AI about '+recipe.name);d.panel.classList.add('ai-recipe-menu');const list=document.createElement('div');list.className='ai-choice-list';
 for(const job of ['convert','like','out']){const b=document.createElement('button');b.type='button';b.className='ai-choice';const [choiceLabel,choiceLine]={convert:['Change this recipe','Less spicy, dairy-free, quicker…'],like:['Would my family like it?','A quick check against our tastes'],out:['I’m out of an ingredient','Get a swap for what’s missing']}[job],choiceTitle=document.createElement('span');choiceTitle.className='ai-choice-title';choiceTitle.textContent=choiceLabel;b.append(choiceTitle);{const sub=document.createElement('span');sub.className='ai-choice-line';sub.textContent=choiceLine;b.append(sub)}b.setAttribute('aria-label',choiceLabel);b.onclick=()=>{d.navigate=true;d.close();setTimeout(()=>openAiJobDialog(job,recipe),0)};list.append(b)}
 d.panel.append(list);
}
// One record per pasted recipe, built like the import review, Off menu, with step tags as links.
// New AI recipes go to an app-made "AI recipes" group under Other groups (not weekly), created on first use.
function ensureAiRecipesGroup(){
 const existing=cats.find(cat=>cat.toLocaleLowerCase()==='ai recipes');if(existing)return existing;
 const name='AI recipes';cats=[...cats,name];persist();const values=JSON.parse(localStorage.getItem(GROUP_ROTATION_KEY)||'{}');values[groupIdentity(name,true)]=false;localStorage.setItem(GROUP_ROTATION_KEY,JSON.stringify(values));persist();return name;
}
function aiImportRecord(raw){
 const details=completeRecipeFields(raw),record={...details,name:details.name||raw.name||'AI recipe',labels:recipeImportTags(raw),...recipeImportStatus(raw,false),groceryDefaultAll:true,url:recipeImportUrl(raw),sourceUrl:recipeImportSourceUrl(raw),importSourceId:raw.importSourceId,recipeSageId:'',recipeImportPending:false};
 if(raw.aiStepTags){const links=askAiStepLinks(record,raw.aiStepTags);if(links)record.ingredientStepLinks=links}return record;
}
function splitAiAnswer(text){
 const clean=String(text||'').replace(/\r/g,'');const starts=[...clean.matchAll(/^\s*(?:#{1,6}\s*)?(?:\*\*)?Title:/gim)].map(m=>m.index);
 if(starts.length<2)return [clean];return starts.map((at,i)=>clean.slice(at,starts[i+1]??clean.length));
}
function restrictionNote(flags){const note=document.createElement('div');note.className='import-restriction-flags';note.setAttribute('role','note');const title=document.createElement('strong');title.textContent='Check for your restrictions';const list=document.createElement('ul');for(const f of flags){const li=document.createElement('li');li.textContent=f.line+' ('+f.label+')';list.append(li)}note.append(title,list);return note}
async function reviewAiAnswer(answer){
 const parts=splitAiAnswer(answer),items=[];for(const part of parts)items.push(askAiItemFromAnswer(part));
 const pending=aiPending(),original=items.length===1&&['convert','like'].includes(pending?.job)?aiFindRecipe(pending.recipeId):null;
 if(items.length>1){openAiMultiReview(items);return}
 let replace=false,mode='copy';if(original){mode=await chooseAiSaveMode(original);if(!mode)return;replace=mode!=='copy'}
 const item=items[0];if(replace){item.aiReplacesRecipeId=String(original.id);item.aiReplaceMode=mode;item.name=original.name}else item.aiTargetGroup=ensureAiRecipesGroup();item.aiReturnToGroups=true;
 await groupHistorySettled;await editorHistorySettled;await reviewRecipeImportItems([item],'Ask AI');setAiPending(null);
 const flags=restrictionConflicts(item.ingredients);
 const place=()=>{const card=document.querySelector('#editor .meal-card-edit-mode'),fields=document.querySelector('#editor .meal-editor-fields');if(!card&&!fields)return;
  let anchor=card;
  if(replace){let note=document.querySelector('#editor .ai-replace-note');if(!note){note=document.createElement('p');note.className='ai-replace-note';note.textContent=mode==='replace'?'Saving replaces '+original.name+'. The original isn’t kept.':'Saving updates '+original.name+'. The original is kept, and you can switch back from the recipe page.'}if(card){if(card.nextElementSibling!==note)card.after(note);anchor=note}else if(!note.isConnected)fields.prepend(note)}
  if(flags.length){let n=document.querySelector('#editor .import-restriction-flags');if(!n)n=restrictionNote(flags);if(anchor){if(anchor.nextElementSibling!==n)anchor.after(n)}else if(!n.isConnected)fields.prepend(n)}};
 place();requestAnimationFrame(()=>requestAnimationFrame(place));setTimeout(place,300);
}
function chooseAiSaveMode(original){return new Promise(resolve=>{
 const d=recipeImportDialog('Save the new version');d.panel.classList.add('ai-save-mode');let done=false;const finish=v=>{if(done)return;done=true;d.close();resolve(v)};
 const list=document.createElement('div');list.className='ai-choice-list';
 for(const [value,label,line]of [['update','Update '+original.name,'Your original is kept. You can switch back any time.'],['replace','Replace '+original.name,'The original isn’t kept.'],['copy','Save as a new recipe','']]){const b=document.createElement('button');b.type='button';b.className='ai-choice';const t=document.createElement('span');t.className='ai-choice-title';t.textContent=label;b.append(t);if(line){const sub=document.createElement('span');sub.className='ai-choice-line';sub.textContent=line;b.append(sub)}b.setAttribute('aria-label',label);b.onclick=()=>{d.navigate=true;finish(value)};list.append(b)}
 d.panel.append(list);const watch=new MutationObserver(()=>{if(!d.panel.isConnected){watch.disconnect();finish(null)}});watch.observe(document.body,{childList:true,subtree:true});
})}
function openAiMultiReview(items){
 const d=recipeImportDialog(items.length+' recipes');d.panel.classList.add('ai-multi-review');const chosen=new Set(items.map((_,i)=>i));
 const list=document.createElement('div');list.className='ai-multi-list';
 items.forEach((item,i)=>{const row=document.createElement('label');row.className='ai-multi-row';const check=document.createElement('input');check.type='checkbox';check.checked=true;check.setAttribute('aria-label','Add '+item.name);check.onchange=()=>{if(check.checked)chosen.add(i);else chosen.delete(i);add.disabled=!chosen.size;add.textContent=chosen.size===1?'Save 1 recipe':'Save '+chosen.size+' recipes'};
  const text=document.createElement('span');text.className='ai-multi-text';const name=document.createElement('strong');name.textContent=item.name;text.append(name);const flags=restrictionConflicts(item.ingredients);if(flags.length){const warn=document.createElement('span');warn.className='ai-multi-flag';warn.textContent='Check: '+flags.map(f=>f.line).join(', ');text.append(warn)}
  row.append(check,text);list.append(row)});
 const actions=document.createElement('div');actions.className='ai-send-actions';const add=document.createElement('button');add.type='button';add.className='smallbtn ai-primary';add.textContent='Save '+items.length+' recipes';actions.append(add);
 add.onclick=()=>{const picked=items.filter((_,i)=>chosen.has(i));if(!picked.length)return;snapshot();const cat=ensureAiRecipesGroup();for(const raw of picked){const record=aiImportRecord(raw);meals.push({...record,id:id++,cat,rotation:false})}persist();setAiPending(null);d.navigate=true;d.close();renderList();showServingUndoToast((picked.length===1?'Saved 1 recipe':'Saved '+picked.length+' recipes')+' to '+cat)};
 d.panel.append(list,actions);
}
// Editor save of an "Update <recipe>" draft: copy the reviewed content into the original (and its shared
// copies), keep its groups/status/favorites, keep grocery choices for unchanged lines, drop the draft.
// Recipe versions (2026-11-19): "Update" keeps the replaced content as meal.aiAltVersion (kind 'original'),
// so the recipe page can switch back or discard it; "Replace" keeps no copy. Content fields only.
const AI_VERSION_FIELDS=['ingredients','instructions','prep','cook','total','marinate','notes','recipeNotes','ingredientStepLinks','url','sourceUrl'];
// Needs Adjusting is PER VERSION (2026-11-23): each version keeps its own flag + note; a new converted version starts without one.
const AI_VERSION_FLAG_FIELDS=['needsTweaking','needsTweakingNote'];
function aiRecipeContent(meal){const out={};for(const key of [...AI_VERSION_FIELDS,...AI_VERSION_FLAG_FIELDS])if(Object.hasOwn(meal,key)&&meal[key]!==undefined)out[key]=JSON.parse(JSON.stringify(meal[key]));return out}
function clearedVersionFlags(){return Object.fromEntries(AI_VERSION_FLAG_FIELDS.map(key=>[key,undefined]))}
function versionFlagPatch(alt){return Object.fromEntries(AI_VERSION_FLAG_FIELDS.map(key=>[key,Object.hasOwn(alt,key)?alt[key]:undefined]))}
// Older converted recipes: while viewing the converted version the stored flag still belonged to the original.
// Move it into the saved original once, so the converted version starts clean and switching back shows it again.
function migrateVersionFlags(meal){
 const alt=meal?.aiAltVersion;if(!alt||alt.kind!=='original'||alt.flagsV1===true)return false;
 for(const key of AI_VERSION_FLAG_FIELDS){if(Object.hasOwn(meal,key)&&meal[key]!==undefined)alt[key]=meal[key];delete meal[key]}alt.flagsV1=true;return true;
}
// One time (2026-11-23): "removed" automatic reminders recorded before suppressions were time-stamped come back.
// Several recipes had them switched off without the person choosing it; a reminder can be removed again from the editor.
function releaseLegacyAutoSuppressions(){
 const key='mealRotationAutoSuppressReleasedV1';try{if(localStorage.getItem(key)==='1')return false}catch(e){return false}
 let changed=false;for(const meal of meals){if(!Array.isArray(meal.makeAheadTasks))continue;const kept=meal.makeAheadTasks.filter(task=>!(task&&task.autoSuppressed===true&&!task.autoSuppressedAt));if(kept.length!==meal.makeAheadTasks.length){changed=true;if(kept.length)meal.makeAheadTasks=kept;else delete meal.makeAheadTasks}}
 try{localStorage.setItem(key,'1')}catch(e){}if(changed)try{persist()}catch(e){}return changed;
}
function migrateAllVersionFlags(){releaseLegacyAutoSuppressions();let changed=false;for(const meal of meals)if(migrateVersionFlags(meal))changed=true;if(changed)try{persist()}catch(e){}return changed}
// Saved grocery choices are never rewritten: lines that existed keep their state; only new lines get a suggestion.
function remapSelectionsAfterContentChange(meal,oldLines=[],dropId=null){
 try{const key='mealRotationSelectedIngredientsV1',sel=JSON.parse(localStorage.getItem(key)||'{}'),lines=(meal.ingredients||[]).map(l=>String(l)),before=new Set(oldLines.map(String)),suggested=new Set(suggestedGroceryLines(meal));let changed=false;
  for(const copy of mealLinkedCopies(meal)){const prev=sel[String(copy.id)];if(!Array.isArray(prev))continue;const kept=new Set(prev);sel[String(copy.id)]=lines.filter(l=>before.has(l)?kept.has(l):suggested.has(l));changed=true}
  if(dropId!=null&&Object.hasOwn(sel,String(dropId))){delete sel[String(dropId)];changed=true}if(changed)localStorage.setItem(key,JSON.stringify(sel))}catch(e){}
}
function mergeAiReplacement(saved){
 const original=aiFindRecipe(saved?.aiReplacesRecipeId);if(!saved)return false;const mode=saved.aiReplaceMode==='replace'?'replace':'update';delete saved.aiReplacesRecipeId;delete saved.aiReplaceMode;if(!original){persist();return false}
 migrateVersionFlags(original);const patch={...clearedVersionFlags()};for(const key of AI_VERSION_FIELDS)patch[key]=Object.hasOwn(saved,key)?saved[key]:undefined;
 // Keep the true original: converting again replaces the converted text, never the saved original.
 if(mode==='update'&&original.aiAltVersion?.kind!=='original')patch.aiAltVersion={kind:'original',flagsV1:true,savedAt:new Date().toISOString(),...aiRecipeContent(original)};
 const oldLines=[...(original.ingredients||[])];assignSharedRecipeFields(original,patch);remapSelectionsAfterContentChange(original,oldLines,saved.id);
 meals=meals.filter(m=>m!==saved);persist();showServingUndoToast((mode==='replace'?'Replaced ':'Updated ')+original.name);return true;
}
function switchRecipeVersion(meal){
 migrateVersionFlags(meal);const alt=meal?.aiAltVersion;if(!alt)return;snapshot();const current={kind:alt.kind==='original'?'converted':'original',flagsV1:true,savedAt:new Date().toISOString(),...aiRecipeContent(meal)},patch={...versionFlagPatch(alt)};
 for(const key of AI_VERSION_FIELDS)patch[key]=Object.hasOwn(alt,key)?alt[key]:undefined;patch.aiAltVersion=current;
 const oldLines=[...(meal.ingredients||[])];assignSharedRecipeFields(meal,patch);remapSelectionsAfterContentChange(meal,oldLines);persist();
}
// Discard the version being viewed: the saved other version becomes the recipe.
function discardRecipeVersion(meal){migrateVersionFlags(meal);const alt=meal?.aiAltVersion;if(!alt)return;snapshot();const patch={...versionFlagPatch(alt)};for(const key of AI_VERSION_FIELDS)patch[key]=Object.hasOwn(alt,key)?alt[key]:undefined;patch.aiAltVersion=undefined;const oldLines=[...(meal.ingredients||[])];assignSharedRecipeFields(meal,patch);remapSelectionsAfterContentChange(meal,oldLines);persist()}
const refreshViewerAfterUndo=()=>{if(typeof recipeViewer!=='undefined'&&recipeViewer)renderRecipeViewer()};
function openRecipeVersionDialog(meal,onDone){
 const showingConverted=meal.aiAltVersion?.kind==='original',d=recipeImportDialog(showingConverted?'Changed recipe':'Original recipe');d.panel.classList.add('ai-version-dialog');
 const list=document.createElement('div');list.className='ai-choice-list';
 const add=(label,line,action)=>{const b=document.createElement('button');b.type='button';b.className='ai-choice';const t=document.createElement('span');t.className='ai-choice-title';t.textContent=label;b.append(t);if(line){const sub=document.createElement('span');sub.className='ai-choice-line';sub.textContent=line;b.append(sub)}b.setAttribute('aria-label',label);b.onclick=()=>{d.navigate=true;d.close();action();onDone?.()};list.append(b)};
 add(showingConverted?'Switch to the original recipe':'Switch to the changed recipe',showingConverted?'The changed version is saved.':'The original version is saved.',()=>{switchRecipeVersion(meal);showServingUndoToast(showingConverted?'Showing the original':'Showing the changed recipe',refreshViewerAfterUndo)});
 add(showingConverted?'Discard the changed recipe':'Discard the original recipe','',()=>{discardRecipeVersion(meal);showServingUndoToast(showingConverted?'Changed recipe discarded':'Original recipe discarded',refreshViewerAfterUndo)});
 d.panel.append(list);
}
let aiTastesOpen=false,aiPasteOpen=false;
function renderAskAiPage(list){
 const page=document.createElement('section');page.className='ask-ai-page';
 const title=document.createElement('h2');title.className='view-page-title';title.textContent='Ask AI';page.append(title);
 const pending=aiPending();
 // Waiting answer card first, when a request was sent; otherwise a quiet "Paste an answer" row at the end.
 const paste=document.createElement('div');paste.className='ai-paste-card';
 const pasteHead=document.createElement('div');pasteHead.className='ai-paste-head';const pasteTitle=document.createElement('strong');pasteTitle.textContent=pending?(aiTargetKey()==='claude'?'Paste Claude’s answer':'Paste the AI’s answer'):'Paste an answer';pasteHead.append(pasteTitle);
 let pasteJob=null;if(pending){const clear=document.createElement('button');clear.type='button';clear.className='iconbtn ai-paste-clear';setIconButton(clear,'cancel','Clear waiting request');clear.onclick=()=>{setAiPending(null);aiPasteOpen=false;renderList({readOnly:true})};pasteHead.append(clear);pasteJob=document.createElement('p');pasteJob.className='ai-paste-job';pasteJob.textContent=AI_JOBS[pending.job]+(pending.recipeName?' · '+pending.recipeName:'')}
 const answer=document.createElement('textarea');answer.rows=5;answer.placeholder='Paste the whole answer from '+aiTargetName();answer.setAttribute('aria-label','Paste the answer');
 const err=document.createElement('p');err.className='recipe-bulk-error';err.setAttribute('role','status');
 const review=document.createElement('button');review.type='button';review.className='smallbtn recipe-review-action ai-review';review.textContent='Review recipe';
 review.onclick=async()=>{err.textContent='';try{splitAiAnswer(answer.value).forEach(askAiItemFromAnswer)}catch(e){err.textContent=e.message;return}await reviewAiAnswer(answer.value)};
 const pasteBody=document.createElement('div');pasteBody.className='ai-paste-body';const reviewRow=document.createElement('div');reviewRow.className='ai-review-row';reviewRow.append(review);pasteBody.append(answer,err,reviewRow);
 if(pending||aiPasteOpen){paste.append(pasteHead);if(pasteJob)paste.append(pasteJob);paste.append(pasteBody)}else{const row=document.createElement('button');row.type='button';row.className='ai-paste-open';row.textContent='Paste an answer';row.onclick=()=>{aiPasteOpen=true;renderList({readOnly:true});requestAnimationFrame(()=>document.querySelector('.ai-paste-card textarea')?.focus({preventScroll:true}))};paste.append(row)}
 if(pending)page.append(paste);
 const section=(label,jobs)=>{const box=document.createElement('section');box.className='ai-section';const head=document.createElement('div');head.className='master-group-section-toggle ai-section-head';const name=document.createElement('span');name.className='master-group-section-name';name.textContent=label;head.append(name);box.append(head);
  const rows=document.createElement('div');rows.className='ai-job-list';for(const job of jobs){const b=document.createElement('button');b.type='button';b.className='ai-job';b.dataset.aiJob=job;const t=document.createElement('span');t.textContent=AI_JOBS[job];const arrow=document.createElement('span');arrow.className='ai-job-arrow';arrow.setAttribute('aria-hidden','true');arrow.innerHTML='<svg viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg>';b.append(t,arrow);b.onclick=()=>openAiJobDialog(job);rows.append(b)}box.append(rows);page.append(box)};
 section('New ideas',['fridge','write']);section('About a recipe',['convert','like','out']);
 if(!pending)page.append(paste);
 // Family tastes: collapsed by default (right-side chevron, like other cards).
 const tastes=document.createElement('section');tastes.className='ai-tastes master-category-card';const toggle=document.createElement('button');toggle.type='button';toggle.className='ai-tastes-toggle';toggle.setAttribute('aria-expanded',String(aiTastesOpen));const tName=document.createElement('span');tName.textContent='Family tastes';const restrictionSummary=familyTastes.restrictions.trim().replace(/\s*[\n;]+\s*/g,', ');const tSummary=document.createElement('span');tSummary.className='ai-tastes-summary';tSummary.textContent=aiTastesOpen||!restrictionSummary?'':restrictionSummary.charAt(0).toUpperCase()+restrictionSummary.slice(1);const chev=document.createElement('span');chev.className='ai-chevron';chev.setAttribute('aria-hidden','true');chev.innerHTML='<svg viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>';toggle.append(tName,tSummary,chev);toggle.onclick=()=>{aiTastesOpen=!aiTastesOpen;renderList({readOnly:true})};tastes.append(toggle);
 if(aiTastesOpen){const body=document.createElement('div');body.className='ai-tastes-body';
  for(const [key,label,placeholder,rows]of [['likes','What we like','e.g. Asian flavors, very savory, not too sweet, weeknight-friendly',3],['restrictions','Restrictions','e.g. no dairy, no soy',2],...(aiTargetKey()==='copy'?[]:[['link',aiTargetName()+' project link','Optional: opens this instead of the home page',1]])]){const wrap=document.createElement('label');wrap.className='recipe-import-field family-tastes-field';const text=document.createElement('span');text.textContent=label;const field=rows>1?document.createElement('textarea'):document.createElement('input');if(rows>1)field.rows=rows;else{field.type='url';field.inputMode='url'}field.placeholder=placeholder;const tk=aiTargetKey();field.value=key==='link'?(tk==='claude'?familyTastes.claudeLink:familyTastes.links?.[tk])||'':familyTastes[key]||'';field.setAttribute('aria-label',label);field.oninput=()=>saveFamilyTastes(key==='link'?(tk==='claude'?{...familyTastes,claudeLink:field.value}:{...familyTastes,links:{...familyTastes.links,[tk]:field.value}}):{...familyTastes,[key]:field.value});wrap.append(text,field);body.append(wrap)}
  tastes.append(body)}
 page.append(tastes);list.append(page);
}

// Settings edits remain reversible until Save is selected.