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
  if(target){if(!cleanupRecipeInstructions(recipeImportInstructionValue(target)).instructions.some(block=>block.type==='step'))target.recipeInstructions=card.recipeInstructions}
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
 return {recipeImportReferences:mergeRecipeImportReferences(recipeImportLinkedReferences(r),cleanup.related,noteParts.related),name:normalizeRecipeText(r.name||r.title||''),ingredients:recipeImportIngredients(r).map(ingredientLine).filter(Boolean),instructions:cleanup.instructions.map(cleanInstructionBlock),notes:noteParts.notes,prep:recipeImportMinutes(r.prepTime??r.prep_time??r.activeTime),cook:recipeImportMinutes(r.cookTime??r.cook_time),total:recipeImportMinutes(r.totalTime??r.total_time),marinate,originalRecipeUrl};
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
 const view=recipeViewer;if(!meal.recipeImportPending){view.importMessage='Instructions are missing. Use Settings → Data & Backups → Refresh Recipes from RecipeSage with your export, or add them in Edit meal.';renderRecipeViewer();return}const tab=view.activeTab,controller=new AbortController();view.importController=controller;view.importMessage='Importing recipe details…';renderRecipeViewer();
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

function restoreState(state){if(state.recipePhotoUndo){try{restoreRecipePhotoReferences(state.recipePhotoUndo.refs)}catch(e){}return}if(state.scheduleChangeUndo)state=restoreScheduleUndoState(state);if(state.groupUndoGrocery)state=restoreGroupGroceryUndo(state);const wasRestoring=restoringRotationCalendars;restoringRotationCalendars=true;try{if(Object.hasOwn(state,'groupIdentities')){if(state.groupIdentities===null)localStorage.removeItem(GROUP_IDENTITIES_KEY);else localStorage.setItem(GROUP_IDENTITIES_KEY,state.groupIdentities)}if(Object.prototype.hasOwnProperty.call(state,'lastRotationBefore')){try{if(state.lastRotationBefore===null)localStorage.removeItem('mealRotationLastRotationBeforeV1');else if(typeof state.lastRotationBefore==='string')localStorage.setItem('mealRotationLastRotationBeforeV1',state.lastRotationBefore)}catch(e){}}if(!restoreMasterGroupOrder(state.masterGroupOrder))return;cats=state.cats;active=state.active;meals=state.meals;if(Array.isArray(state.mealPlans)&&state.mealPlans.length){mealPlans=JSON.parse(JSON.stringify(state.mealPlans));activePlanId=state.activePlanId||mealPlans[0].id;showMealPlanTabs=!!state.showMealPlanTabs;autoPinTopCategories=true;}else saveActiveMealPlan();checkedIngredients=new Set(state.checkedIngredients||[]);groceryOccurrenceChecks=state.groceryOccurrenceChecks?JSON.parse(JSON.stringify(state.groceryOccurrenceChecks)):{version:1,checks:{}};groceryCheckStorageInvalid=false;saveGroceryOccurrenceChecks();if(state.weekdayCategories)weekdayCategories=state.weekdayCategories;if(state.weekdayMealOverrides)weekdayMealOverrides=state.weekdayMealOverrides;if(state.weekdayRecipeFilters){weekdayRecipeFilters=state.weekdayRecipeFilters;saveWeekdayRecipeFilters();}if(state.pinnedCats)pinnedCats=state.pinnedCats;if(state.expandedCats)expandedCats=state.expandedCats;if(typeof state.autoPinTopCategories==='boolean')autoPinTopCategories=true;if(typeof state.applyPinsToAllTabs==='boolean'){applyPinsToAllTabs=state.applyPinsToAllTabs;localStorage.setItem('mealRotationApplyPinsAllTabsV1',String(applyPinsToAllTabs))}if(['all','current','across','none'].includes(state.masterOpenMode))masterOpenMode=state.masterOpenMode;if(typeof state.masterPinsOverride==='boolean')masterPinsOverride=state.masterPinsOverride;saveMasterOpeningPrefs();if(state.startWeekday)startWeekday=state.startWeekday;if(state.topCounts)topCounts=state.topCounts;categoryColors=state.categoryColors&&typeof state.categoryColors==='object'?{...state.categoryColors}:{};saveCategoryColors();weekdayColors=state.weekdayColors&&typeof state.weekdayColors==='object'?{...state.weekdayColors}:deriveWeekdayColors(categoryColors);saveWeekdayColors();id=Math.max(0,...meals.map(m=>Number(m.id)||0))+1;editId=null;newRecipeDraftId=null;editorCategoryBaseline=null;editorDraftCategories=null;stopMealEditorPositioning();menuCat=null;if(state.skippedCookingState)restoreSkippedCookingState(state.skippedCookingState);if(state.bulkRecipeUndoLabels){recipeLabelCatalog=[...state.bulkRecipeUndoLabels];saveRecipeLabelCatalog()}if(state.bulkRecipeUndoSelections)restoreBulkRecipeSelections(state.bulkRecipeUndoSelections);if(state.groupUndoIngredientSelections){const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const [key,value]of Object.entries(state.groupUndoIngredientSelections)){if(value===null)delete selected[key];else selected[key]=value}localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected))}if(state.bulkRecipeUndoNewSelections?.length){const values=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const key of state.bulkRecipeUndoNewSelections)if(!meals.some(m=>String(m.id)===key))delete values[key];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(values))}if(state.bulkRecipeUndoExclusions){for(const key of state.bulkRecipeUndoExclusions)masterGroceryExcludedMealKeys.add(key);saveMasterGroceryMealExclusions()}persist();try{localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));saveWeekdayCategories();saveWeekdayMealOverrides();saveTopCounts();localStorage.setItem('mealRotationPinnedCategoriesV1',JSON.stringify(pinnedCats));localStorage.setItem('mealRotationApplyPinsAllTabsV1',String(applyPinsToAllTabs));localStorage.setItem('mealRotationExpandedCategoriesV1',JSON.stringify(expandedCats));localStorage.setItem('mealRotationStartWeekdayV1',startWeekday);localStorage.setItem('mealRotationAutoPinTopCategoriesV1',String(autoPinTopCategories))}catch(e){}resetGroceriesForNewTopMeals(new Set(getDisplayedWeekdayMeals().map(({meal})=>String(meal.id))));render()}finally{restoringRotationCalendars=wasRestoring}}
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
async function exportRecipeBackup(data){data=JSON.parse(JSON.stringify(data));let result=data;try{result=await recipePhotoStorage.appendBackup(data)}catch(e){result={...data,photos:{version:1,items:[],missing:[...recipePhotoStorage.refs(data)],warnings:['Photo export failed. Recipes are still backed up.']}}}let blob;try{blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'})}catch(e){result={...data,photos:{version:1,items:[],missing:[...recipePhotoStorage.refs(data)],warnings:['Photo encoding failed; recipe data is still backed up.']}};blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'})}const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='meal-rotation-backup.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);if(result.photos?.warnings?.length)showAppMessage('Recipe backup downloaded. Some optional photos were unavailable: '+result.photos.warnings.join(' '))}


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
 const raw=Array.isArray(json)?json:json.version===2&&Array.isArray(json.meals)?json.meals:Array.isArray(json.recipes)?json.recipes:Array.isArray(json.meals)&&json.recipes===undefined?json.meals:Array.isArray(json['@graph'])?json['@graph']:Array.isArray(json.items)?json.items:[json];
 return raw.filter(x=>x&&typeof x==='object'&&!Array.isArray(x)).flatMap(r=>{
  if(r['@graph'])return recipeImportItems(r);
  const name=String(r.name||r.title||r.recipeName||'').trim();if(!name)return [];
  if(r['@type']&&!String(Array.isArray(r['@type'])?r['@type'].join(' '):r['@type']).toLowerCase().includes('recipe'))return [];
  return [{...r,name,recipeInstructions:resolveInstructions(recipeImportInstructionValue(r)),recipeCategory:recipeImportTags(r),recipeIngredient:r.recipeIngredient??r.ingredients??[],prepTime:r.prepTime??r.prep_time??r.preparationTime??'',cookTime:r.cookTime??r.cook_time??'',totalTime:r.totalTime??r.total_time??'',url:r.url||r.recipeUrl||r.link||r.source_url||r.sourceUrl||'',identifier:r.identifier||r.id||r.uid||r.uuid||'',linkedRecipes:r.linkedRecipes??r.linkedMeals??r.linkedRecipeIds??r.linkedMealIds??r.relatedRecipes??r.relatedMeals??[],importSourceId:r.importSourceId||(r.uid?'paprika:'+r.uid:r.title&&r.id?'mela:'+r.id:'')}];
 });
}
function recipeImportTags(r){
 const values=[r.recipeCategory,r.labels,r.keywords,r.categories,r.tags,r.cat].flatMap(value=>Array.isArray(value)?value:typeof value==='string'?value.split(/[,;|]/):[]);
 return [...new Set(values
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
function showRecipeImportSelection(items,filename){
 const tags=[...new Set(items.flatMap(recipeImportTags))].sort((a,b)=>a.localeCompare(b,undefined,{sensitivity:'base'}));
 const overlay=document.createElement('div');overlay.id='recipeImportDialog';overlay.style.cssText='position:fixed;inset:0;z-index:16000;background:#0008;padding:16px;display:flex;align-items:center;justify-content:center';
 const box=document.createElement('div');box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-labelledby','recipeImportTitle');box.style.cssText='width:100%;max-width:520px;max-height:min(88vh,800px);border-radius:14px;background:white;color:#242424;box-shadow:0 10px 32px #0004;padding:20px;display:flex;flex-direction:column;min-height:0;gap:10px';
 const title=document.createElement('h2');title.id='recipeImportTitle';title.textContent='Choose meal groups';title.style.cssText='font-size:21px;margin:0';box.append(title);
 const subtitle=document.createElement('p');subtitle.textContent=items.length+' recipes found in '+filename+'. Choose which source tags or lists should become meal groups.';subtitle.style.cssText='font-size:14px;color:#666;margin:0';box.append(subtitle);
 const summary=document.createElement('p');summary.style.cssText='font-size:13px;color:#666;margin:0';box.append(summary);
 const toolbar=document.createElement('div');toolbar.style.cssText='display:flex;gap:8px;align-items:center';
 const all=document.createElement('button');all.type='button';all.className='smallbtn';all.textContent='Select all';
 const none=document.createElement('button');none.type='button';none.className='smallbtn';none.textContent='Select none';
 toolbar.append(all,none);box.append(toolbar);
 const list=document.createElement('div');list.style.cssText='overflow-y:auto;min-height:70px;max-height:45vh;padding:6px 2px;border-top:1px solid #e5e5e5;border-bottom:1px solid #e5e5e5';const checks=[];
 for(const tag of tags){const row=document.createElement('label');row.style.cssText='display:flex;align-items:center;gap:10px;padding:9px 4px;font-size:16px';const cb=document.createElement('input');cb.type='checkbox';cb.checked=false;cb.style.cssText='width:21px;height:21px;flex:0 0 21px';const name=document.createElement('span');name.textContent=tag;name.style.flex='1';const count=document.createElement('span');count.textContent=String(items.filter(x=>recipeImportTags(x).includes(tag)).length);count.style.cssText='font-size:12px;color:#888';row.append(cb,name,count);list.append(row);checks.push({tag,cb});cb.onchange=updateSummary;}
 if(!tags.length){list.textContent='This file has no recipe tags. All imported meals will go into Unassigned.';list.style.fontSize='14px';all.disabled=true;none.disabled=true;}
 box.append(list);
 const notes=document.createElement('p');notes.style.cssText='font-size:13px;color:#666;margin:0';notes.textContent='Checked source tags become meal groups. Meals without a checked group go to Unassigned.';box.append(notes);const importRotation=document.createElement('input');importRotation.type='checkbox';importRotation.checked=true;stage2FormField(box,'Add grouped imports to rotation',importRotation);
 const footer=document.createElement('div');footer.style.cssText='display:flex;justify-content:flex-end;gap:10px;margin-top:6px';
 const cancel=document.createElement('button');cancel.type='button';cancel.className='smallbtn';cancel.textContent='Cancel';
 const apply=document.createElement('button');apply.type='button';apply.className='smallbtn';apply.textContent='Import recipes';apply.style.cssText='background:#e8eefb;border-color:#aac0df;font-weight:600';
 footer.append(cancel,apply);box.append(footer);overlay.append(box);document.body.append(overlay);
 function updateSummary(){const chosen=new Set(checks.filter(x=>x.cb.checked).map(x=>x.tag));const unassigned=items.filter(x=>!recipeImportTags(x).some(t=>chosen.has(t))).length;summary.textContent=chosen.size+' groups selected · '+unassigned+' recipes will go into Unassigned';}
 all.onclick=()=>{checks.forEach(x=>x.cb.checked=true);updateSummary()};none.onclick=()=>{checks.forEach(x=>x.cb.checked=false);updateSummary()};cancel.onclick=()=>overlay.remove();overlay.onclick=e=>{if(e.target===overlay)overlay.remove()};
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
   const categories=[...new Set(matching.map(catFor))];
   if(!categories.length){categories.push('');unassigned++}
   if(!firstCategory)firstCategory=categories[0];
   const prep=recipeImportMinutes(r.prepTime??r.activeTime);
   const total=recipeImportMinutes(r.totalTime);
   const cook=recipeImportMinutes(r.cookTime);
   const importedLabels=[...new Set(recipeImportTags(r).map(tag=>{const key=labelKey(tag);if(!canonicalLabels.has(key))canonicalLabels.set(key,tag.trim().replace(/\s+/g,' '));return canonicalLabels.get(key)}))];
   const importedDetails=completeRecipeFields(r);
   const base={recipeImportReferences:importedDetails.recipeImportReferences,recipeImportPending:!importedDetails.instructions.some(b=>b.type==='step')&&!!(recipeImportUrl(r)||importedDetails.originalRecipeUrl),instructions:importedDetails.instructions,notes:importedDetails.notes,originalRecipeUrl:importedDetails.originalRecipeUrl,name:r.name.trim(),labels:importedLabels,rotation:importRotation.checked,groceryDefaultAll:true,keepAsIdea:!importRotation.checked,prep,cook,total:total!==''?total:(prep!==''&&cook!==''?Number(prep)+Number(cook):''),marinate:importedDetails.marinate,url:recipeImportUrl(r),sourceUrl:recipeImportSourceUrl(r),recipeSageId:/^[0-9a-f]{8}-/.test(sourceId)?sourceId:'',importSourceId:sourceId,ingredients:importedDetails.ingredients};
   const group=categories.length>1?'imported-'+(sourceId||nextId):'';
   categories.forEach(cat=>{const meal={...base,id:nextId++,cat,linkGroup:group,ingredients:[...base.ingredients]};if(!cat){meal.rotation=false;meal.keepAsIdea=true}newMeals.push(meal);enrichIds.push(meal.id)});
   if(sourceId)existingIds.add(sourceId);
   added++;
  }
  if(!added&&!enriched){overlay.remove();recipeImportNotice('All recipes in this file have already been imported.');return}
  const nextActive=firstCategory||active;
  const encoded=JSON.stringify({cats:nextCats,active:nextActive,meals:newMeals});
  try{localStorage.setItem('mealRotationDataV1',encoded)}catch(err){
   recipeImportNotice('Import could not be saved. Your browser may be low on storage. No existing meals were changed.');return;
  }
  snapshot();cats=nextCats;meals=newMeals;id=nextId;recipeLabelCatalog=[...canonicalLabels.values()];saveRecipeLabelCatalog();active=nextActive;showTop=false;editId=null;menuCat=null;
  expandedCats=[...new Set([...expandedCats,...addedCats])];
  try{localStorage.setItem('mealRotationExpandedCategoriesV1',JSON.stringify(expandedCats))}catch(e){}
  if(unassigned){masterExpansionInitialized=true;masterExpandedCategories.add('')}
  overlay.remove();render();
  recipeImportNotice('Imported '+added+' recipes across '+addedCats.length+' new groups.'+(unassigned?' '+unassigned+' saved in Unassigned.':'')+(enriched?' Added missing details to '+enriched+' existing recipe records.':'')+(skipped?' Skipped '+skipped+' duplicate recipes.':'')+(enrichIds.some(id=>!instructionBlocks(meals.find(m=>m.id===id)?.instructions).some(b=>b.type==='step'))?' Some imports have no reliable cooking instructions yet. Available ingredients were preserved. Supported source URLs will be checked in the background; use Refresh Recipes from RecipeSage with your export for any still incomplete recipes.':''),meals.filter(m=>m.recipeImportReferences?.length&&(enrichIds.includes(m.id)||items.some(r=>recipeImportIdentity(r)===m.importSourceId))));
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

// Refresh only recipe content; schedules, recipe identity and all custom fields stay intact.
function recipeSageRefreshPlan(items,library=meals){
 const ids=r=>recipeRepairIds(r,true).filter(id=>recipeSageUuidPattern.test(id));
 const urls=r=>recipeRepairUrls(r).map(url=>correctedRecipeSageUrl({url})).filter(url=>{try{return /^(?:www\.|android\.)?recipesage\.com$/i.test(new URL(url).hostname)}catch(e){return false}});
 const sources=items.map(raw=>({raw,ids:ids(raw),urls:urls(raw),title:recipeReferenceTitle(raw.name)}));
 const rows=[],skipped=[];
 for(const meal of library){
  const savedIds=ids(meal),savedUrls=urls(meal),title=recipeReferenceTitle(meal.name);
  let matches=sources.filter(s=>s.ids.some(id=>savedIds.includes(id)));
  if(!matches.length)matches=sources.filter(s=>s.urls.some(url=>savedUrls.includes(url)));
  if(!matches.length){const names=sources.filter(s=>s.title===title);if(names.length===1&&library.filter(m=>recipeReferenceTitle(m.name)===title).length===1&&!(savedIds.length&&names[0].ids.length&&!names[0].ids.some(id=>savedIds.includes(id))))matches=names;}
  if(matches.length!==1){skipped.push(meal.id);continue}
  const source=matches[0];
  if(source.ids.length>1||(savedIds.length&&source.ids.length&&savedIds.some(id=>!source.ids.includes(id)))){skipped.push(meal.id);continue}
  // Separate copies in multiple groups may share a proven source identity.
  const details=completeRecipeFields(source.raw);
  if(!details.ingredients.length||!details.instructions.some(b=>b.type==='step'&&b.text.trim())){skipped.push(meal.id);continue}
  const replacement={...meal,ingredients:details.ingredients,instructions:details.instructions};
  const oldNotes=String(meal.notes||''),cleaned=recipeRepairLegacyNotes(meal,library).notes;
  const importedBefore=meal.recipeSageImportedNotes,rawNotes=source.raw.recipeNotes??source.raw.notes??source.raw.note??source.raw.description;
  // Unknown/personal notes are never replaced. Strip only proven legacy footer text.
  if(details.notes&&(!oldNotes.trim()||oldNotes===importedBefore||oldNotes===details.notes||(typeof rawNotes==='string'&&oldNotes===rawNotes)||cleaned==='')){
   replacement.notes=details.notes;replacement.recipeSageImportedNotes=details.notes;
  }else if(cleaned!==null&&cleaned!==oldNotes)replacement.notes=cleaned;
  // Do not invalidate saved manual associations or completed cooking tokens.
  const after=cookingItemTokens(replacement);
  const ingredients=new Set(after.ingredients.map(x=>x.token)),steps=new Set(after.steps.map(x=>x.token));
  const links=Array.isArray(meal.ingredientStepLinks)?meal.ingredientStepLinks:[];
  if(links.some(l=>!steps.has(l.step)||!Array.isArray(l.ingredients)||l.ingredients.some(t=>!ingredients.has(t)))||Object.values(cookingSessions.occurrences).some(s=>String(s.context.mealId)===String(meal.id)&&(s.steps.some(t=>!steps.has(t))||s.ingredients.some(t=>!ingredients.has(t))||(s.autoIngredients||[]).some(t=>!ingredients.has(t))||Object.keys(s.ingredientOverrides||{}).some(t=>!ingredients.has(t))))){skipped.push(meal.id);continue}
  rows.push({meal,replacement});
 }
 return {rows,skipped};
}
async function storeRecipeSageSafetyBackup(data,database){
 // IndexedDB transaction completion plus a read-back is required before any recipe write.
 if(typeof indexedDB==='undefined')throw Error('Safety backup is unavailable. No recipes changed.');
 const text=JSON.stringify(data),key=Date.now()+'-'+Math.random().toString(36).slice(2);
 const db=await new Promise((resolve,reject)=>{const request=indexedDB.open(database,1);request.onupgradeneeded=()=>request.result.createObjectStore('backups');request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(Error('Safety backup could not be created. No recipes changed.'));request.onblocked=()=>reject(Error('Safety backup is unavailable. No recipes changed.'))});
 try{
  await new Promise((resolve,reject)=>{const tx=db.transaction('backups','readwrite');tx.objectStore('backups').put(text,key);tx.oncomplete=resolve;tx.onabort=tx.onerror=()=>reject(Error('Safety backup could not be saved. No recipes changed.'))});
  const saved=await new Promise((resolve,reject)=>{const tx=db.transaction('backups','readonly'),r=tx.objectStore('backups').get(key);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(Error('Safety backup could not be checked. No recipes changed.'))});
  if(saved!==text)throw Error('Safety backup verification failed. No recipes changed.');
  return text;
 }finally{db.close()}
}
function buildRecipeSageRefresh(backup){
 const box=document.createElement('section');box.id='recipeSageRefresh';box.style.cssText='margin-top:12px;display:grid;gap:8px';
 const title=document.createElement('strong');title.textContent='Refresh Recipes from RecipeSage';
 const explanation=document.createElement('p');explanation.style.margin='0';explanation.textContent='Choose a RecipeSage export to refresh matching recipes. Your customizations and personal notes stay intact. A complete safety backup is saved and downloaded automatically first. Incomplete or uncertain matches are skipped.';
 const choose=document.createElement('button');choose.type='button';choose.textContent='Choose RecipeSage export file';
 const input=document.createElement('input');input.type='file';input.accept='.json,application/json,*/*';input.hidden=true;
 const apply=document.createElement('button');apply.type='button';apply.textContent='Refresh Recipes';apply.disabled=true;
 const result=document.createElement('p');result.style.margin='0';result.setAttribute('role','status');result.setAttribute('aria-live','polite');
 box.append(title,explanation,choose,input,apply,result);let items=null,generation=0;
 const memoryState=()=>JSON.stringify([captureState(),cookingSessions,occurrenceScales,recipeViewPrefs,timeDisplayPrefs]);
 choose.onclick=()=>input.click();
 input.onchange=async()=>{const file=input.files?.[0],current=++generation;items=null;apply.disabled=true;if(!file)return;result.textContent='Reading export…';try{if(file.size>60000000)throw Error('Choose an export smaller than 60 MB.');const parsed=await recipeImportReadFile(file);if(current!==generation)return;if(!parsed.length)throw Error('No recipes were found in this file.');items=parsed;result.textContent=file.name;apply.disabled=false}catch(e){if(current===generation)result.textContent=e.message}};
 apply.onclick=async()=>{
  if(!items)return;apply.disabled=choose.disabled=true;
  try{
   if(editId!==null||recipeViewer||backupRestoreReloadPending||recipePageLeaving)throw Error('Close the recipe viewer or editor before refreshing.');
   const storage=backup.capture(),memory=memoryState();backup.validate(storage);
   const core=JSON.parse(storage.mealRotationDataV1);if(JSON.stringify(core)!==JSON.stringify({cats,active,meals}))throw Error('Saved data changed. Reload the app before refreshing.');
   const plan=recipeSageRefreshPlan(items),next={...core,meals:meals.map(m=>plan.rows.find(r=>r.meal===m)?.replacement||m)},encoded=JSON.stringify(next);
   backup.validate({...storage,mealRotationDataV1:encoded});
   if(!plan.rows.length){result.textContent='0 recipes refreshed. '+plan.skipped.length+' skipped.';return}
   result.textContent='Saving safety backup…';
   const text=await storeRecipeSageSafetyBackup({version:2,...core,storage},backup.database);
   if(!box.isConnected||JSON.stringify(backup.capture())!==JSON.stringify(storage)||memoryState()!==memory||editId!==null||recipeViewer||backupRestoreReloadPending||recipePageLeaving)throw Error('Saved data changed. No recipes refreshed. Try again.');
   const url=URL.createObjectURL(new Blob([text],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='meal-rotation-before-recipesage-refresh-'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
   // One synchronous, atomic localStorage write; no reconciliation of unrelated data.
   try{localStorage.setItem('mealRotationDataV1',encoded)}catch(e){throw Error('Refresh could not be saved. No recipes changed. Your safety backup was kept.')}
   for(const {meal,replacement} of plan.rows){Object.assign(meal,replacement);cookingRecipeStates.set(String(meal.id),JSON.stringify({id:meal.id,ingredients:meal.ingredients,instructions:meal.instructions,ingredientStepLinks:meal.ingredientStepLinks}))}
   result.textContent=mealPersistence.unsaved?'Refresh is only in memory and has not been saved. Use Retry Save before closing this page.':plan.rows.length+' recipes refreshed. '+plan.skipped.length+' skipped.';
  }catch(e){result.textContent=e.message||'Refresh stopped. No recipes changed.'}finally{apply.disabled=!items;choose.disabled=false}
 };
 return box;
}
function openRecipeImportFilePicker(){
 const input=document.createElement('input');input.type='file';input.accept='.json,application/json,*/*';
 input.onchange=async()=>{const file=input.files?.[0];if(!file)return;
  try{
   if(/\.json$/i.test(file.name)||file.type==='application/json'){
    const backup=JSON.parse(await file.text());
    if(backup?.version===2&&Array.isArray(backup.meals)&&Array.isArray(backup.cats)){
     const replacement=normalizeImportedBackup(backup);validateBackupCore(startupCore(backup));validateBackupStorage(replacement);
     if(confirm('This is a full Meal Rotation backup. Restore all recipes, plans and settings? This replaces the app data in this browser. Export a backup first if you need to keep it.'))await restoreVersion2Backup(backup);
     return;
    }
   }
   const items=await recipeImportReadFile(file);if(!items.length){recipeImportNotice('No recipes were found in this export. Check that the file contains recipe information.');return}showRecipeImportSelection(items,file.name)
  }
  catch(e){recipeImportNotice('Could not read the recipe export. '+(e.message||'No meals were changed.')+' No meals were changed.')}
 };input.click();
}
async function restoreVersion2Backup(backup){
 validateBackupCore(startupCore(backup));
 const replacement=normalizeImportedBackup(backup);validateBackupStorage(replacement);
 const preparation=await prepareOptionalBackupPhotos(backup);if(preparation.cancelled)return;
 const finish=()=>{restoreBackupStorage(replacement);recipePhotoNotice(preparation.warnings);mealPersistence.reload()};
 restoreBackupStorage(replacement,{id:'backup-restore',kind:'backup-restore',ownerId:null,retry:finish});
 recipePhotoNotice(preparation.warnings);mealPersistence.reload();
}
function openRecipeImportSourcePicker(){
 const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;z-index:16100;display:flex;align-items:center;justify-content:center;background:#0008;padding:18px';
 const box=document.createElement('div');box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label','Import recipes');box.style.cssText='width:100%;max-width:460px;padding:22px;background:white;color:#242424;border-radius:14px;box-shadow:0 12px 35px #0004;display:flex;flex-direction:column;gap:12px';
 const heading=document.createElement('h2');heading.textContent='Import recipes';heading.style.cssText='font-size:20px;margin:0 0 4px';box.append(heading);
 function action(label,desc,fn){const b=document.createElement('button');b.type='button';b.className='smallbtn';b.style.cssText='display:block;width:100%;text-align:left;padding:12px 14px';b.textContent=label;const hint=document.createElement('div');hint.textContent=desc;hint.style.cssText='font-size:12px;color:#666;margin-top:5px';b.append(hint);b.onclick=()=>{overlay.remove();fn()};box.append(b)}
 action('Choose recipe export file','RecipeSage, Paprika, Mela, Trello, CSV, JSON, HTML, or ZIP.',openRecipeImportFilePicker);
 action('Trello board link','Try a public board link. Trello may require exporting board JSON instead.',openRecipeImportTrelloLink);
 const cancel=document.createElement('button');cancel.type='button';cancel.className='smallbtn';cancel.textContent='Cancel';cancel.style.alignSelf='flex-end';cancel.onclick=()=>overlay.remove();box.append(cancel);
 overlay.append(box);document.body.append(overlay);overlay.onclick=e=>{if(e.target===overlay)overlay.remove()};box.querySelector('button')?.focus({preventScroll:true});overlay.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();overlay.remove()}if(e.key==='Tab'){const buttons=[...box.querySelectorAll('button')],first=buttons[0],last=buttons.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}};
}
function openRecipeImportTrelloLink(){
 const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;z-index:16100;display:flex;align-items:center;justify-content:center;background:#0008;padding:18px';
 const box=document.createElement('div');box.style.cssText='width:100%;max-width:475px;padding:22px;background:white;color:#242424;border-radius:14px;display:flex;flex-direction:column;gap:12px';
 const title=document.createElement('h2');title.textContent='Import from Trello board';title.style.cssText='font-size:20px;margin:0';box.append(title);
 const input=document.createElement('input');input.type='url';input.placeholder='https://trello.com/b/…';input.setAttribute('aria-label','Trello board URL');input.style.cssText='width:100%;border:1px solid #ccc;border-radius:8px;padding:12px';box.append(input);
 const hint=document.createElement('p');hint.textContent='A Trello link may not be readable directly from this app, particularly for private boards. You can always export your board as JSON in Trello and import that file instead.';hint.style.cssText='font-size:13px;color:#666;margin:0';box.append(hint);
 const status=document.createElement('p');status.style.cssText='font-size:13px;color:#666;margin:0';box.append(status);
 const actions=document.createElement('div');actions.style.cssText='display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end';
 const choose=document.createElement('button');choose.className='smallbtn';choose.textContent='Choose JSON export';choose.onclick=()=>{overlay.remove();openRecipeImportFilePicker()};
 const cancel=document.createElement('button');cancel.className='smallbtn';cancel.textContent='Cancel';cancel.onclick=()=>overlay.remove();
 const read=document.createElement('button');read.className='smallbtn';read.textContent='Try board link';read.style.background='#e8eefb';
 actions.append(choose,cancel,read);box.append(actions);overlay.append(box);document.body.append(overlay);
 read.onclick=async()=>{
  let url;try{url=new URL(input.value.trim())}catch(e){status.textContent='Enter a complete Trello board URL.';return}
  if(url.protocol!=='https:'||!['trello.com','www.trello.com'].includes(url.hostname)||!/^\/b\/[a-z0-9]{6,}/i.test(url.pathname)){status.textContent='Enter a link beginning with https://trello.com/b/';return}
  const code=url.pathname.split('/')[2];const jsonURL='https://trello.com/b/'+encodeURIComponent(code)+'.json';
  read.disabled=true;status.textContent='Trying to read board…';
  try{const response=await fetch(jsonURL,{credentials:'omit',signal:AbortSignal.timeout(12000)});if(!response.ok)throw new Error('Board not accessible');
    const raw=await response.json(),items=recipeImportItems(raw);if(!items.length)throw new Error('No cards found');overlay.remove();showRecipeImportSelection(items,'Trello board '+code);
  }catch(e){status.textContent='Trello blocked direct access or the board is private. In Trello, open the board menu → Print, export, and share → Export as JSON, then choose that file here.'}
  finally{read.disabled=false}
 };
}
// Settings edits remain reversible until Save is selected.