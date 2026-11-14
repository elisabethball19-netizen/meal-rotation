/* Shared inline in both apps: recovery must run before migrations or autosave. */
// These migration helpers must be defined before rotation.js initializes saved meals.
function compactIngredientFractions(value){
  const glyphs={'1/2':'½','1/3':'⅓','2/3':'⅔','1/4':'¼','3/4':'¾','1/8':'⅛','3/8':'⅜','5/8':'⅝','7/8':'⅞'};
  let result=String(value??'');
  // Some imported recipes lose the space in a mixed number: 11/2 = 1½.
  // Restrict this repair to quantities at the start of a line or after a range dash,
  // so fractions inside ingredient names, dates and URLs are not altered.
  result=result.replace(/(^|[–—-]\s*)([1-9])([1-7])\/(2|3|4|8)(?=$|[^\w/])/g,(all,prefix,whole,num,den)=>{
    const frac=num+'/'+den;
    return glyphs[frac]?prefix+whole+glyphs[frac]:all;
  });
  return result.replace(/(^|[^\w/])(\d+)\s+(1\/2|1\/3|2\/3|1\/4|3\/4|1\/8|3\/8|5\/8|7\/8)(?=$|[^\w/])/g,(all,pre,whole,frac)=>pre+whole+glyphs[frac])
    .replace(/(^|[^\w/])(1\/2|1\/3|2\/3|1\/4|3\/4|1\/8|3\/8|5\/8|7\/8)(?=$|[^\w/])/g,(all,pre,frac)=>pre+glyphs[frac]);
}
// One-time, non-destructive migration for ingredients saved before fraction formatting.
// Preserve grocery selection matches by migrating the associated stored strings too.
function migrateSavedIngredientFractions(){
 const flag='mealRotationCompactFractionsMigratedV2';
 if(localStorage.getItem(flag)==='true')return;
 const updates={};
 try{
  const raw=localStorage.getItem('mealRotationDataV1');
  if(!raw)return;
  const data=JSON.parse(raw);
  if(!Array.isArray(data.meals))return;
  let changed=false;
  for(const meal of data.meals){
   if(!Array.isArray(meal.ingredients))continue;
   meal.ingredients=meal.ingredients.map(item=>{
    if(typeof item!=='string')return item;
    const next=compactIngredientFractions(item);
    if(next!==item)changed=true;
    return next;
   });
  }
  if(changed)updates.mealRotationDataV1=JSON.stringify(data);
  const selectedRaw=localStorage.getItem('mealRotationSelectedIngredientsV1');
  if(selectedRaw){
   const selected=JSON.parse(selectedRaw);
   if(selected&&typeof selected==='object'&&!Array.isArray(selected)){
    let selectedChanged=false;
    for(const [key,items] of Object.entries(selected)){
     if(!Array.isArray(items))continue;
     selected[key]=items.map(item=>{
      if(typeof item!=='string')return item;
      const next=compactIngredientFractions(item);
      if(next!==item)selectedChanged=true;
      return next;
     });
    }
    if(selectedChanged)updates.mealRotationSelectedIngredientsV1=JSON.stringify(selected);
   }
  }
  const checksRaw=localStorage.getItem('mealRotationCheckedIngredientsV1');
  if(checksRaw){
   const checks=JSON.parse(checksRaw);
   if(Array.isArray(checks)){
    const normalized=[...new Set(checks.map(x=>typeof x==='string'?compactIngredientFractions(x):x))];
    if(JSON.stringify(normalized)!==JSON.stringify(checks))updates.mealRotationCheckedIngredientsV1=JSON.stringify(normalized);
   }
  }
  // Save a rollback copy before changing existing records.
  if(Object.keys(updates).length){
   const originals={};for(const key of Object.keys(updates))originals[key]=localStorage.getItem(key);
   localStorage.setItem('mealRotationFractionMigrationBackupV2',JSON.stringify(originals));
   for(const [key,value] of Object.entries(updates))localStorage.setItem(key,value);
  }
  localStorage.setItem(flag,'true');
 }catch(e){ /* Leave the migration pending if storage is unavailable. */ }
}
// Optional immutable images. This layer never writes recipe/localStorage data.
const recipePhotoStorage=(()=>{
 // Legacy backup/restore compatibility only; no recipe-photo display, resizing or upload UI.
 const test=typeof TEST_PREFIX==='string'&&TEST_PREFIX==='mealRotationTestSandboxV1:',name=test?'mealRotationTestRecipePhotosV1':'mealRotationRecipePhotosV1',limit=256*1024,budget=40*1024*1024;
 const valid=id=>typeof id==='string'&&/^rp1-[a-f0-9]{64}$/.test(id);let connection=null;
 function deadline(work,message,ms=5000,abort=()=>{}){return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{abort();reject(Error(message))},ms);Promise.resolve(work).then(value=>{clearTimeout(timer);resolve(value)},error=>{clearTimeout(timer);reject(error)})})}
 function open(){if(connection)return connection;connection=new Promise((resolve,reject)=>{let request,expired=false;const timer=setTimeout(()=>{expired=true;reject(Error('Photo storage did not respond.'))},3500);try{if(!window.indexedDB)throw Error('Photo storage is unavailable.');request=indexedDB.open(name,1);request.onupgradeneeded=()=>{if(!request.result.objectStoreNames.contains('photos'))request.result.createObjectStore('photos')};request.onblocked=()=>{clearTimeout(timer);expired=true;reject(Error('Photo storage is busy. Close other copies of this app and try again.'))};request.onerror=()=>{clearTimeout(timer);reject(Error('Photo storage is unavailable.'))};request.onsuccess=()=>{clearTimeout(timer);if(expired){request.result.close();return}const db=request.result;db.onclose=()=>{connection=null};db.onversionchange=()=>{db.close();connection=null};resolve(db)}}catch(error){clearTimeout(timer);reject(error)}}).catch(error=>{connection=null;throw error});return connection}
 async function read(id){if(!valid(id))return null;const db=await open();let tx;const value=await deadline(new Promise((resolve,reject)=>{tx=db.transaction('photos','readonly');const r=tx.objectStore('photos').get(id);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(Error('Photo could not be read.'));tx.onabort=()=>reject(Error('Photo read was interrupted.'))}),'Photo read did not complete.',5000,()=>{try{tx?.abort()}catch(e){}});return value instanceof Blob&&value.type==='image/jpeg'&&value.size<=limit&&await idFor(value)===id?value:null}
 // Portable SHA-256 keeps references usable on offline/non-HTTPS origins too.
 function sha256(bytes){const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2],h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];const data=new Uint8Array(Math.ceil((bytes.length+9)/64)*64);data.set(bytes);data[bytes.length]=128;const view=new DataView(data.buffer);view.setUint32(data.length-8,Math.floor(bytes.length/0x20000000));view.setUint32(data.length-4,(bytes.length*8)>>>0);const r=(v,n)=>(v>>>n)|(v<<(32-n)),w=new Int32Array(64);for(let offset=0;offset<data.length;offset+=64){for(let i=0;i<16;i++)w[i]=view.getInt32(offset+i*4);for(let i=16;i<64;i++){const a=w[i-15],b=w[i-2];w[i]=(w[i-16]+(r(a,7)^r(a,18)^(a>>>3))+w[i-7]+(r(b,17)^r(b,19)^(b>>>10)))|0}let[a,b,c,d,e,f,g,z]=h;for(let i=0;i<64;i++){const t=(z+(r(e,6)^r(e,11)^r(e,25))+((e&f)^(~e&g))+K[i]+w[i])|0,u=((r(a,2)^r(a,13)^r(a,22))+((a&b)^(a&c)^(b&c)))|0;z=g;g=f;f=e;e=(d+t)|0;d=c;c=b;b=a;a=(t+u)|0}for(const [i,v]of [a,b,c,d,e,f,g,z].entries())h[i]=(h[i]+v)|0}return h.map(v=>(v>>>0).toString(16).padStart(8,'0')).join('')}
 async function idFor(blob){const bytes=new Uint8Array(await deadline(blob.arrayBuffer(),'Photo bytes could not be read.'));return 'rp1-'+(globalThis.crypto?.subtle?Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join(''):sha256(bytes))}
 async function put(items){for(const item of items)if(!valid(item.id)||!(item.blob instanceof Blob)||item.blob.type!=='image/jpeg'||item.blob.size>limit||await idFor(item.blob)!==item.id)throw Error('Photo could not be verified.');const db=await open();let tx;await deadline(new Promise((resolve,reject)=>{tx=db.transaction('photos','readwrite');tx.oncomplete=resolve;tx.onabort=()=>reject(Error('Photo write was interrupted or storage is full.'));tx.onerror=()=>{try{tx.abort()}catch(e){}};try{for(const item of items)tx.objectStore('photos').put(item.blob,item.id)}catch(error){try{tx.abort()}catch(e){}reject(error)}}),'Photo write did not complete.',5000,()=>{try{tx?.abort()}catch(e){}})}
 async function image(blob){const url=URL.createObjectURL(blob),img=new Image();try{await deadline(new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=()=>reject(Error('This image could not be decoded.'));img.src=url}),'Image decoding timed out.',8000);if(!img.naturalWidth||!img.naturalHeight)throw Error('This image has no usable dimensions.');return {img,close:()=>URL.revokeObjectURL(url)}}catch(e){URL.revokeObjectURL(url);throw e}}
 function refs(data){const ids=new Set(),seen=new Set();function root(value,depth=0){if(!value||depth>64)return;if(typeof value==='string'){if(seen.has(value))return;seen.add(value);try{value=JSON.parse(value)}catch(e){return}}if(!value||typeof value!=='object')return;for(const m of Array.isArray(value.meals)?value.meals:[])if(valid(m?.recipePhotoId))ids.add(m.recipePhotoId);if(value.lastRotationBefore)root(value.lastRotationBefore,depth+1)}function storage(values){if(!values||typeof values!=='object')return;root(values.mealRotationDataV1);root(values.mealRotationLastRotationBeforeV1)}root(data);for(const key of ['storage','originalStorage','unsaved'])storage(data?.[key]);for(const tx of Array.isArray(data?.failedTransactions)?data.failedTransactions:[]){storage(tx?.baseStorage);for(const p of Array.isArray(tx?.proposals)?tx.proposals:[])storage(p?.storage)}return ids}
 function base64(bytes){let text='';for(let i=0;i<bytes.length;i+=8192)text+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(text)}
 async function appendBackup(data){const ids=[...refs(data)];if(!ids.length)return data;const photos={version:1,items:[],missing:[],warnings:[]};let size=0,unavailable=false;for(const id of ids){try{if(unavailable)throw Error('Photo storage is unavailable.');if(photos.items.length>=4096)throw Error('Photo bundle limit reached.');const blob=await read(id);if(!blob)throw Error('An image is missing.');if(size+blob.size>budget)throw Error('Photo bundle size limit reached.');if(await idFor(blob)!==id)throw Error('An image could not be verified.');photos.items.push({id,type:'image/jpeg',data:base64(new Uint8Array(await blob.arrayBuffer()))});size+=blob.size}catch(e){photos.missing.push(id);if(!photos.warnings.includes(e.message))photos.warnings.push(e.message);if(/storage|respond|busy|read|complete/i.test(e.message))unavailable=true}}return {...data,photos}}
 async function restore(data){const used=refs(data),warnings=[],manifest=data?.photos;if(!manifest){if(used.size)warnings.push('This backup has photo references without image files. Recipe photo display is no longer used.');return warnings}if(manifest.version!==1||!Array.isArray(manifest.items)){return ['Optional photo data was not recognized. Recipes can still be restored.']}if(manifest.items.some(item=>valid(item?.id)&&used.has(item.id)))try{await open()}catch(e){return ['Optional photo storage is unavailable. Recipe content remains usable.']}const items=[],seen=new Set();let total=0;for(const item of manifest.items.slice(0,4096)){try{if(!item||!valid(item.id)||!used.has(item.id)||seen.has(item.id))continue;if(item.type!=='image/jpeg'||typeof item.data!=='string'||item.data.length>Math.ceil(limit/3)*4||!/^[A-Za-z0-9+/]*={0,2}$/.test(item.data))throw Error('Invalid optional photo data.');const raw=atob(item.data),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));if(bytes.length>limit||total+bytes.length>budget)throw Error('Optional photo bundle exceeds its size limit.');if(bytes[0]!==255||bytes[1]!==216||bytes[2]!==255||bytes.at(-2)!==255||bytes.at(-1)!==217)throw Error('Optional photo is not a JPEG.');const blob=new Blob([bytes],{type:'image/jpeg'});if(await idFor(blob)!==item.id)throw Error('Optional photo checksum did not match.');const decoded=await image(blob);try{if(Math.max(decoded.img.naturalWidth,decoded.img.naturalHeight)>1024)throw Error('Optional photo dimensions exceed their limit.')}finally{decoded.close()}items.push({id:item.id,blob});seen.add(item.id);total+=blob.size}catch(e){if(!warnings.includes(e.message))warnings.push(e.message)}}if(manifest.items.length>4096)warnings.push('Some optional photos exceeded the entry limit.');if(items.length)try{await put(items)}catch(e){warnings.push('Photo storage was not available: '+e.message)}if([...used].some(id=>!seen.has(id)))warnings.push('Some photo files are missing. Recipe content remains usable.');return warnings}
 async function clear(){const db=await open();let tx;await deadline(new Promise((resolve,reject)=>{tx=db.transaction('photos','readwrite');tx.objectStore('photos').clear();tx.oncomplete=resolve;tx.onabort=tx.onerror=()=>reject(Error('Test photos could not be cleared.'))}),'Test photo reset timed out.',5000,()=>{try{tx?.abort()}catch(e){}})}
 if(test)window.mealRotationClearTestPhotos=clear;
 return {valid,name,limit,idFor,sha256,read,put,refs,appendBackup,restore:async data=>{try{return await restore(data)}catch(e){return ['Optional photo restoration failed. Recipe content remains usable.']}},test};
})();
function recipePhotoNotice(warnings){if(!warnings?.length)return;try{sessionStorage.setItem(recipePhotoStorage.test?'mealRotationTestPhotoNotice':'mealRotationPhotoNotice','Recipes restored. '+warnings.join(' '))}catch(e){}}

function createMealPersistence(provider){
 const JOURNAL_KEY='mealRotationRecoveryJournalV1';
 let base,readError=null,recovery=false,strict=false,suspended=false,recoveryActions=null,startupValidator=null;
 let original=new Map(),pending=new Map(),failures=new Map(),warning=null,retrying=false,journal=null,journalRaw=null,journalCleanupPending=false,journalReplacementVerified=false;
 const owned=key=>typeof key==='string'&&key.startsWith('mealRotation')&&!key.startsWith('mealRotationTestSandboxV1:')&&!key.startsWith('mealRotationTESTONLY__')&&key!==JOURNAL_KEY;
 const copy=value=>JSON.parse(JSON.stringify(value));
 function readRaw(){
  const result=new Map(),unreadable=[];let firstError=null;
  try{for(let i=0;i<base.length;i++){const key=base.key(i);if(!owned(key))continue;try{const value=base.getItem(key);if(value!==null)result.set(key,value)}catch(error){unreadable.push(key);firstError||=error}}}catch(error){unreadable.push('*');firstError||=error}
  if(firstError){const error=Error(firstError.message||'Saved data could not be read');error.readableRecords=result;error.unreadableKeys=unreadable;throw error}return result;
 }
 function parseJournal(raw){const value=JSON.parse(raw);if(value?.version!==1||!value.originalStorage||Array.isArray(value.originalStorage)||typeof value.originalStorage!=='object'||Object.values(value.originalStorage).some(v=>typeof v!=='string'))throw Error('Unreadable recovery journal');return value}
 // Journaling is optional: never trim the current rollback snapshot to make it fit.
 // Keep the complete current attempt in memory even when durable storage is full.
 function saveJournal(value){
  journal=value;
  value.previousAttempts=Array.isArray(value.previousAttempts)?value.previousAttempts.slice(-6):[];
  const encode=()=>JSON.stringify(value),fits=text=>new Blob([text]).size<=50*1024;
  try{
   let encoded=encode();
   while(!fits(encoded)&&value.previousAttempts.length){value.previousAttempts.shift();encoded=encode()}
   if(!fits(encoded))return false;
   try{base.setItem(JOURNAL_KEY,encoded)}
   catch(error){
    if(error.name!=='QuotaExceededError'&&error.code!==22&&error.code!==1014)return false;
    // Retry once with the oldest half discarded (all when only one remains).
    value.previousAttempts.splice(0,Math.ceil(value.previousAttempts.length/2));
    encoded=encode();base.setItem(JOURNAL_KEY,encoded);
   }
   if(base.getItem(JOURNAL_KEY)!==encoded)return false;
   journalRaw=encoded;return true;
  }catch(error){return false}
 }
 function matchesRecords(actual,expected){return !!expected&&typeof expected==='object'&&!Array.isArray(expected)&&actual.size===Object.keys(expected).length&&Object.entries(expected).every(([key,value])=>typeof value==='string'&&actual.get(key)===value)}
 try{base=provider()}catch(e){readError=e;recovery=true}
 if(base){
  try{original=readRaw()}catch(e){if(e.readableRecords)original=e.readableRecords;readError=e;recovery=true}
  // Read the journal independently so denied app-record reads do not hide earlier recovery data.
  try{journalRaw=base.getItem(JOURNAL_KEY);if(journalRaw!==null)journal=parseJournal(journalRaw)}catch(e){readError||=e;recovery=true}
 }
 const button=(label,action)=>{const b=document.createElement('button');b.type='button';b.className='smallbtn';b.textContent=label;b.style.minHeight='44px';b.onclick=action;return b};
 function download(data,name){try{const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return true}catch(e){const message='The recovery export could not be downloaded. Keep this page open and try again.';if(recovery){const status=document.getElementById('mealRecoveryStatus');if(status)status.textContent=message}else notify(message);return false}}
 function capture(){try{return readRaw()}catch(e){readError=e;recovery=true;showRecovery();return e.readableRecords||new Map()}}
 function controls(root){return [...root.querySelectorAll('input,textarea,select')].map(el=>({id:el.id,name:el.name,label:el.getAttribute('aria-label')||el.closest('label')?.textContent||'',type:el.type,value:el.type==='file'?'':el.value,checked:el.checked,selected:el.multiple?[...el.selectedOptions].map(o=>o.value):undefined,files:el.type==='file'?[...el.files].map(f=>({name:f.name,type:f.type,size:f.size})):undefined}))}
 function editorDrafts(){return [...document.querySelectorAll('#editor .editor,[data-recipe-edit-draft],[data-recovery-draft],[role="dialog"]:not(#mealDataRecovery)')].map((root,index)=>{const provider=root.mealRecoveryDraft;try{return {ownerId:provider?.ownerId||root.id||'dialog-'+index,kind:provider?.kind||'form',data:provider?.capture?copy(provider.capture()):null,controls:controls(root)}}catch(e){return {ownerId:provider?.ownerId||root.id||'dialog-'+index,controls:controls(root),captureError:String(e.message||e)}}})}
 function liveEditor(ownerId){return [...document.querySelectorAll('#editor .editor,[data-scheduled-recipe-draft],[data-viewer-recipe-draft]')].map(el=>el.mealRecoveryDraft).find(p=>p?.ownerId===ownerId)}
 function hasDrafts(){return [...document.querySelectorAll('#editor .editor,[data-recipe-edit-draft],[data-recovery-draft]')].some(root=>root.mealRecoveryDraft?.dirty?root.mealRecoveryDraft.dirty():true)}
 function exportRecovery(){
  const drafts=editorDrafts(),incomplete=drafts.some(d=>d.captureError);
  const data={format:'meal-rotation-recovery-v2',exportedAt:new Date().toISOString(),readError:readError?String(readError.message||readError):null,unreadableKeys:readError?.unreadableKeys||[],storage:Object.fromEntries(capture()),originalStorage:journal?.originalStorage||Object.fromEntries(original),unsaved:Object.fromEntries(pending),failedTransactions:[...failures.values()].map(f=>copy(f.record)),editorDrafts:drafts,recoveryJournal:journal||journalRaw,notes:'storage contains readable persisted records; originalStorage contains the pre-recovery journal snapshot or last known saved snapshot; failedTransactions also retain their own pre-operation baseStorage; unsaved contains pending writes/removals (null means remove); failedTransactions contains rolled-back proposals; editorDrafts contains current raw text, selections and supported draft metadata. Files themselves are not embedded.'};
  const finish=value=>{let ok=download(value,'meal-rotation-recovery.json');if(!ok&&value!==data)ok=download(data,'meal-rotation-recovery.json');if(ok&&incomplete){const message='Some draft metadata could not be exported. Raw form controls were included, but keep this page open; the export may be incomplete.';if(recovery)document.getElementById('mealRecoveryStatus').textContent=message;else notify(message)}};
  if(recipePhotoStorage.refs(data).size)recipePhotoStorage.appendBackup(data).then(value=>{if(value.photos)value.notes+=' Optional recipe photos are included when available.';finish(value)},()=>finish(data));else finish(data);
 }
 function unresolved(){return pending.size>0||failures.size>0||journalCleanupPending}
 function notify(message='Changes have not been saved to this browser. Keep this page open. Retry Save or export persisted records, pending writes, failed proposals, and current editor text for recovery.'){
  if(recovery||suspended)return;
  if(!warning){warning=document.createElement('section');warning.id='mealSaveWarning';warning.setAttribute('role','alert');warning.style.cssText='position:sticky;top:0;z-index:40000;background:#fff3d6;color:#422d00;border:1px solid #c69b44;border-radius:10px;padding:12px;margin:0 0 12px;';const text=document.createElement('p');text.style.margin='0 0 8px';const actions=document.createElement('div');actions.style.cssText='display:flex;gap:8px;flex-wrap:wrap';actions.append(button('Retry Save',retry),button('Export Data for Recovery',exportRecovery));warning.append(text,actions);document.body.prepend(warning)}
  warning.firstElementChild.textContent=message;
 }
 function clearWarning(){if(!unresolved()){warning?.remove();warning=null}}
 function write(key,value){
  if(recovery||suspended)return;
  key=String(key);value=value===null?null:String(value);
  if(strict){try{if(value===null)base.removeItem(key);else base.setItem(key,value);if(value===null)original.delete(key);else original.set(key,value)}catch(e){notify('The change was not saved. Existing saved data is being preserved. Retry the save or export your data.');throw e}return}
  const deferred=pending.size>0;pending.set(key,value);
  if(deferred){notify();return}
  try{if(value===null)base.removeItem(key);else base.setItem(key,value);pending.delete(key);if(value===null)original.delete(key);else original.set(key,value);clearWarning()}catch(e){notify()}
 }
 const storage={
  getItem(key){if(recovery)return null;key=String(key);if(pending.has(key))return pending.get(key);try{return base.getItem(key)}catch(e){readError=e;recovery=true;showRecovery();return null}},
  setItem(key,value){write(key,String(value))},removeItem(key){write(key,null)},
  get length(){return keys().length},key(index){return keys()[index]??null}
 };
 function keys(){if(recovery)return [];const result=new Set();try{for(let i=0;i<base.length;i++){const key=base.key(i);if(owned(key))result.add(key)}}catch(e){readError=e;recovery=true;showRecovery();return []}for(const [key,value]of pending)if(owned(key)){if(value===null)result.delete(key);else result.add(key)}return [...result]}
 function inspect(check){startupValidator=check;if(recovery)return;try{
  check(Object.fromEntries(original));
  // Verify the whole replacement before any migration, normalization, or automatic app write.
  if(journalRaw!==null){
   if(journal.replacementCommitted!==true){
    if(!matchesRecords(original,journal.replacement))throw Error('Recovery replacement is incomplete. Original records and earlier recovery information remain available for export or another restore.');
    // Durable proof permits a later startup after normalization or cleanup was interrupted.
    if(!saveJournal({...journal,replacementCommitted:true})){
     // Retire stale completion metadata before migrations can change the verified records.
     base.removeItem(JOURNAL_KEY);
     if(base.getItem(JOURNAL_KEY)!==null)throw Error('The old recovery journal could not be retired. Saving remains paused.');
     journalRaw=null;
    }
   }
   journalReplacementVerified=true;
  }
 }catch(e){readError=e;recovery=true}}
 function transaction(action){
  if(recovery)throw Error('Saved data is unreadable. Use the recovery interface first.');
  if(pending.size)throw Error('There are unsaved changes. Use Retry Save before this operation.');
  const before=capture(),wasStrict=strict;if(recovery)throw Error('Saved data became unreadable. Use recovery before making further changes.');strict=true;
  try{const result=action();clearWarning();return result}
  catch(e){const after=capture();original=new Map(before);pending=new Map();for(const key of new Set([...before.keys(),...after.keys()]))if((before.get(key)??null)!==(after.get(key)??null))pending.set(key,before.get(key)??null);notify('The change was not saved. Your previous data has been kept where possible. Retry saving before closing this page.');throw e}
  finally{strict=wasStrict}
 }
 function offerRetry(action,details){
  const id=details.id,prior=failures.get(id),proposal=copy(details.proposal),record={id,kind:details.kind,ownerId:details.ownerId||null,status:'failed',baseStorage:Object.fromEntries(original),proposals:[...(prior?.record.proposals||[]),{createdAt:new Date().toISOString(),storage:proposal,editorDrafts:editorDrafts()}]};
  failures.set(id,{record,action});notify();
 }
 function resolve(id){failures.delete(id);clearWarning()}
 function cancelOwner(ownerId){for(const [id,failure]of failures)if(failure.record.ownerId===ownerId)failures.delete(id);clearWarning()}
 function matchesBase(record){const current=capture();return ['mealRotationDataV1','mealRotationPlansV1','mealRotationSelectedIngredientsV1'].every(key=>(current.get(key)??null)===(record.baseStorage[key]??null))}
 async function retry(){
  if(retrying)return;retrying=true;
  try{
   if(pending.size){const writes=[...pending].sort(([a],[b])=>(a==='mealRotationDataV1')-(b==='mealRotationDataV1'));for(const [key,value]of writes){if(value===null)base.removeItem(key);else base.setItem(key,value);if(base.getItem(key)!==value)throw Error('Storage did not retain the saved value.')}for(const [key,value]of pending)if(value===null)original.delete(key);else original.set(key,value);pending.clear()}
   for(const [id,failure]of [...failures].sort((a,b)=>Number(!!liveEditor(b[1].record.ownerId))-Number(!!liveEditor(a[1].record.ownerId)))){
    if(failures.get(id)!==failure)continue;
    if(failure.record.ownerId){const editor=liveEditor(failure.record.ownerId);if(!editor)throw Error('The failed editor is no longer open. Export its proposal for recovery, or repeat the original action.');if([...document.querySelectorAll('[role="dialog"]:not(#recipeViewer),[role="alertdialog"]')].some(dialog=>dialog.mealRecoveryDraft!==editor))throw Error('Finish or cancel the open dialog before retrying the editor save.');await editor.save();}
    else{if(hasDrafts())throw Error('Save or explicitly cancel the open editor before retrying this operation.');if(!matchesBase(failure.record))throw Error('Data changed after this failed operation. Its proposal has been kept for export; repeat the original action against the current data.');await failure.action();}
   }
   if(journalCleanupPending){base.removeItem(JOURNAL_KEY);journal=null;journalRaw=null;journalCleanupPending=false}
   clearWarning();
  }catch(e){notify('Changes are still not saved. '+(e.message||'Storage is unavailable.')+' Keep this page open, retry, or export your data.')}
  finally{retrying=false}
 }
 function reload(){if(hasDrafts())throw Error('Unsaved editor changes are still open. Save or cancel them before reloading.');suspended=true;window.dispatchEvent(new Event('mealRotationBeforeStorageReset'));location.reload()}
 function startFresh(){
  // Explicitly confirmed destruction is deletion-only, even at quota or with a bad journal.
  suspended=true;
  window.dispatchEvent(new Event('mealRotationBeforeStorageReset'));
  try{
   const remove=new Set([JOURNAL_KEY]);
   for(let i=0;i<base.length;i++){const key=base.key(i);if(owned(key))remove.add(key)}
   for(const key of remove)base.removeItem(key);
   for(const key of remove)if(base.getItem(key)!==null)throw Error('Browser storage did not delete '+key);
   for(let i=0;i<base.length;i++)if(owned(base.key(i)))throw Error('Some app records could not be deleted.');
   original.clear();pending.clear();failures.clear();journal=null;journalRaw=null;
   journalCleanupPending=false;journalReplacementVerified=false;readError=null;recovery=false;strict=false;
   warning?.remove();warning=null;location.reload();
  }catch(error){recovery=true;readError=error;throw Error('Start Fresh could not finish deleting saved data. Automatic saving remains paused. '+error.message)}
 }
 function replace(data){
  startupValidator(data);
  if(hasDrafts())throw Error('An unsaved editor is still open. Export its draft and explicitly cancel it before replacing saved data.');
  let before,priorJournalRaw;
  // Export may use a partial snapshot; replacement and rollback must never do so.
  try{before=readRaw();priorJournalRaw=base.getItem(JOURNAL_KEY)}catch(error){readError=error;recovery=true;showRecovery();throw Error('Original saved data could not be completely read. No replacement was attempted. '+error.message)}
  let priorJournal=journal;if(!priorJournal&&priorJournalRaw!==null)try{priorJournal=parseJournal(priorJournalRaw)}catch(_){}
  // Keep earlier attempts flat and intact, including pending writes, proposals, and drafts.
  const previousAttempts=Array.isArray(priorJournal?.previousAttempts)?[...priorJournal.previousAttempts]:[];
  if(priorJournal){const previous={...priorJournal};if(Array.isArray(previous.previousAttempts))delete previous.previousAttempts;previousAttempts.push(previous)}
  const nextJournal={version:1,replacementCommitted:false,previousJournalRaw:priorJournal?undefined:priorJournalRaw,previousAttempts,createdAt:new Date().toISOString(),originalStorage:priorJournal?.originalStorage||Object.fromEntries(before),beforeReplacement:Object.fromEntries(before),replacement:data,pendingWrites:Object.fromEntries(pending),failedTransactions:[...failures.values()].map(f=>copy(f.record)),editorDrafts:editorDrafts()};
  if(!saveJournal(nextJournal)){
   // An older journal must not describe this new replacement after a reload.
   try{base.removeItem(JOURNAL_KEY);if(base.getItem(JOURNAL_KEY)!==null)throw Error('Journal was not removed');journalRaw=null}
   catch(error){throw Error('The previous recovery journal could not be retired. No replacement was attempted. '+error.message)}
  }
  try{
   for(const [key,value]of Object.entries(data).sort(([a],[b])=>(a==='mealRotationDataV1')-(b==='mealRotationDataV1')))base.setItem(key,value);
   for(const key of before.keys())if(!Object.hasOwn(data,key))base.removeItem(key);
   const actual=Object.fromEntries(readRaw());if(Object.keys(actual).length!==Object.keys(data).length||Object.entries(data).some(([key,value])=>actual[key]!==value))throw Error('Replacement could not be verified.');startupValidator(actual);
  }catch(e){let failed=false;for(const key of new Set([...before.keys(),...Object.keys(data)]))try{if(before.has(key))base.setItem(key,before.get(key));else base.removeItem(key)}catch(_){failed=true}throw Error('Recovery could not be saved. '+(failed?'Storage prevented complete rollback.':'Original records were restored.')+' The original snapshot is retained '+(journalRaw?'in the recovery journal.':'in memory; keep this page open and export recovery data.'))}
  saveJournal({...nextJournal,replacementCommitted:true});
  original=new Map(Object.entries(data));pending.clear();failures.clear();
  reload();
 }
 function finishStartup(){
  if(!journalRaw||recovery)return;
  if(!journalReplacementVerified){failStartup(Error('Recovery replacement has not been verified. Original recovery information is retained.'));return}
  try{startupValidator(Object.fromEntries(readRaw()))}catch(error){failStartup(error);return}
  try{base.removeItem(JOURNAL_KEY);journal=null;journalRaw=null;journalCleanupPending=false}
  catch(e){journalCleanupPending=true;notify('The original recovery snapshot is still retained. Retry Save to finish recovery cleanup, or export it before closing this page.')}
 }
 function failStartup(error){readError=error;recovery=true;showRecovery()}
 function showRecovery(actions=recoveryActions){
  if(actions)recoveryActions=actions;if(!recovery||!recoveryActions)return;
  let cover=document.getElementById('mealDataRecovery');if(cover)return;
  cover=document.createElement('section');cover.id='mealDataRecovery';cover.setAttribute('role','alertdialog');cover.setAttribute('aria-modal','true');cover.setAttribute('aria-labelledby','mealRecoveryTitle');cover.style.cssText='position:fixed;inset:0;z-index:50000;background:#fff;color:#242424;overflow:auto;padding:24px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start';
  const panel=document.createElement('div');panel.style.cssText='width:100%;max-width:520px;margin-block:auto;flex-shrink:0';const title=document.createElement('h1');title.id='mealRecoveryTitle';title.textContent='Saved data needs recovery';title.style.fontSize='24px';const detail=document.createElement('p');detail.textContent='Meal Rotation could not read its saved data. Automatic saving is paused to protect recoverable information. Export your data before restoring a backup or starting fresh.';const status=document.createElement('p');status.id='mealRecoveryStatus';status.setAttribute('role','status');status.style.overflowWrap='anywhere';status.textContent=readError?.message||'';
  const controls=document.createElement('div');controls.style.cssText='display:flex;gap:10px;flex-wrap:wrap';
  const restore=button('Restore Backup',()=>{const input=document.createElement('input');input.type='file';input.accept='.json,application/json,*/*';input.onchange=async()=>{const file=input.files?.[0];if(!file)return;restore.disabled=fresh.disabled=true;try{const backup=JSON.parse(await file.text()),data=recoveryActions.normalize(backup);recoveryActions.validateCore(backup);recoveryActions.validate(data);const photoWarnings=await recipePhotoStorage.restore(backup);replace(data);recipePhotoNotice(photoWarnings)}catch(e){status.textContent='Backup was not restored: '+e.message}finally{restore.disabled=fresh.disabled=false}};input.click()});
  const fresh=button('Start Fresh',()=>{if(panel.querySelector('[data-start-fresh-confirm]'))return;const confirmation=document.createElement('div');confirmation.dataset.startFreshConfirm='true';const text=document.createElement('p');text.textContent='Starting fresh will delete this app’s saved recipes, plans, and settings in this browser. Export Data for Recovery first if you may need them.';confirmation.append(text,button('Confirm Start Fresh',()=>{try{startFresh()}catch(e){status.textContent=e.message}}),button('Cancel Start Fresh',()=>confirmation.remove()));panel.append(confirmation)});
  controls.append(restore,button('Export Data for Recovery',exportRecovery),fresh);
  if(hasDrafts())controls.append(button('Cancel Open Drafts',()=>{
   if(panel.querySelector('[data-cancel-drafts-confirm]'))return;
   const confirmation=document.createElement('div');confirmation.dataset.cancelDraftsConfirm='true';const text=document.createElement('p');text.textContent='This discards unsaved editor text and selections. Export Data for Recovery first if you need to keep them. Saved records will not be replaced.';
   confirmation.append(text,button('Confirm Cancel Drafts',()=>{for(const root of [...document.querySelectorAll('#editor .editor,[data-recipe-edit-draft],[data-recovery-draft]')]){if(!root.isConnected)continue;if(root.mealRecoveryDraft?.discard)root.mealRecoveryDraft.discard();else root.remove()}for(const dialog of [...document.querySelectorAll('[role="dialog"]:not(#recipeViewer)')])if(dialog!==cover&&!cover.contains(dialog))dialog.remove();confirmation.remove();for(const el of document.body.children)if(el!==cover)el.inert=true;status.textContent='Open drafts were explicitly cancelled. Original saved records remain protected.'}),button('Keep Open Drafts',()=>confirmation.remove()));panel.append(confirmation);
  }));panel.append(title,detail,status,controls);cover.append(panel);document.body.append(cover);for(const el of document.body.children)if(el!==cover)el.inert=true;restore.focus();
 }
 window.addEventListener('beforeunload',event=>{if(unresolved()){event.preventDefault();event.returnValue=''}});
 return {storage,inspect,transaction,offerRetry,resolve,cancelOwner,notify,showRecovery,finishStartup,failStartup,reload,startFresh,editorDrafts,get recovery(){return recovery},get unsaved(){return unresolved()},get paused(){return suspended||recovery}};
}

const mealPersistence=createMealPersistence(()=>window.localStorage);
const mealBulkStorageBase=mealPersistence.storage;
let rotationCalendarTrackingReady=false,restoringRotationCalendars=false;
function bulkRecipeStorageBridge(base){return new Proxy(base,{get(target,key){
 if(bulkRecipeStorageDraft){const draft=bulkRecipeStorageDraft;if(key==='getItem')return k=>draft.get(String(k))??null;if(key==='setItem')return (k,v)=>{draft.set(String(k),String(v))};if(key==='removeItem')return k=>{draft.delete(String(k))};if(key==='key')return i=>[...draft.keys()][Number(i)]??null;if(key==='length')return draft.size;if(key==='clear')return ()=>draft.clear()}
 const value=Reflect.get(target,key,target);return typeof value==='function'?value.bind(target):value;
}})}
function validateWeekSchedule(value){
 const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
 if(!object(value)||value.version!==1||!object(value.slots)||!object(value.order))throw Error('Invalid temporary week schedule');
 const validKey=key=>typeof key==='string'&&['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'].some(day=>key.startsWith(day+'::')&&key.length>day.length+2);
 for(const [key,item] of Object.entries(value.slots)){
  if(!validKey(key)||!object(item)||!['empty','once'].includes(item.kind))throw Error('Invalid temporary meal slot');
  if('groceryChecks'in item)validateGroceryOccurrenceChecks({version:1,checks:item.groceryChecks,quantities:item.groceryQuantities});
  if(item.kind==='once'&&(!object(item.meal)||typeof item.meal.id!=='string'||!item.meal.id.startsWith('once-')||typeof item.meal.name!=='string'||!item.meal.name.trim()||!Array.isArray(item.meal.ingredients)||item.meal.ingredients.some(line=>typeof line!=='string')||item.meal.temporaryMeal!==true))throw Error('Invalid temporary meal');
 }
 if(value.linkedGroceryChecks)validateGroceryOccurrenceChecks({version:1,checks:value.linkedGroceryChecks,quantities:value.linkedGroceryQuantities});
 const ids=Object.values(value.slots).filter(item=>item.kind==='once').map(item=>item.meal.id);if(new Set(ids).size!==ids.length)throw Error('Duplicate temporary meal IDs');
 for(const [day,order] of Object.entries(value.order))if(!validKey(day+'::order')||!Array.isArray(order)||order.some(id=>typeof id!=='string')||new Set(order).size!==order.length)throw Error('Invalid weekday display order');
}
mealPersistence.inspect(validateStartupStorage);
function startupCore(core){return core&&Array.isArray(core.cats)&&!core.cats.length&&Array.isArray(core.meals)&&!core.meals.length?{...core,cats:['__empty_library__']}:core}
function validateStartupStorage(data){validateSavedRecords(data,false)}
// Startup and every replacement share this registry; unknown extension values remain opaque.
function validateSavedRecords(data,requireCore=false){
 const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v),strings=v=>Array.isArray(v)&&v.every(x=>typeof x==='string'),id=v=>typeof v==='string'||Number.isSafeInteger(v),days=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
 const parsed={};
 const objectKeys=['mealRotationWeekdayCategoriesV1','mealRotationWeekdayMealOverridesV1','mealRotationWeekdayRecipeFiltersV1','mealRotationSelectedIngredientsV1','mealRotationTopCountsV1','mealRotationGroupIdentitiesV1','mealRotationWeekdayColorsV1','mealRotationCategoryColorsV1','mealRotationFractionMigrationBackupV2'];
 const nullableObjects=['mealRotationTimeVisibilityV1','mealRotationRecipeViewPrefsV1','mealRotationMakeAheadDisplayV1','mealRotationEditorSectionsV1','mealRotationGroupSectionExpansionV1'];
 const arrayKeys=['mealRotationCheckedIngredientsV1','mealRotationPinnedCategoriesV1','mealRotationExpandedCategoriesV1','mealRotationRecipeLabelCatalogV1','mealRotationGroupDisplayOrderV1','mealRotationMasterGroceryExcludedPlansV1','mealRotationMasterGroceryExcludedMealsV1'];
 const otherKeys=['mealRotationDataV1','mealRotationPlansV1','mealRotationCookingSessionsV1','mealRotationOccurrenceScalesV1','mealRotationGroceryOccurrenceChecksV1','mealRotationCookingTimerV1','mealRotationLastRotationBeforeV1'];
 for(const [key,value]of Object.entries(data)){
  if(typeof value!=='string')throw Error('Invalid saved value: '+key);
  const structured=objectKeys.includes(key)||nullableObjects.includes(key)||arrayKeys.includes(key)||otherKeys.includes(key)||key.startsWith('mealRotationLastTopMealIdsV1:');
  if(!structured)continue;
  try{parsed[key]=JSON.parse(value)}catch(e){throw Error('Unreadable saved JSON: '+key)}
  const v=parsed[key];if(objectKeys.includes(key)&&!object(v)||nullableObjects.includes(key)&&v!==null&&!object(v)||arrayKeys.includes(key)&&!(key==='mealRotationMasterGroceryExcludedPlansV1'||key==='mealRotationMasterGroceryExcludedMealsV1'?Array.isArray(v)&&v.every(id):strings(v))||key.startsWith('mealRotationLastTopMealIdsV1:')&&(!Array.isArray(v)||v.some(x=>!id(x))))throw Error('Invalid saved record type: '+key);
 }
 if(requireCore&&!Object.hasOwn(data,'mealRotationDataV1'))throw Error('Missing recipe collection');
 if(Object.hasOwn(data,'mealRotationDataV1'))validateBackupCore(startupCore(parsed.mealRotationDataV1));
 if(Object.hasOwn(data,'mealRotationPlansV1'))validateBackupCore({...startupCore(parsed.mealRotationDataV1),mealPlans:parsed.mealRotationPlansV1});
 const assignments=[parsed.mealRotationWeekdayCategoriesV1,...(parsed.mealRotationPlansV1?.plans||[]).map(p=>p.weekdayCategories)].filter(Boolean);for(const map of assignments)if(Object.values(map).some(v=>typeof v!=='string'&&!strings(v)))throw Error('Invalid weekday assignments');
 const selected=parsed.mealRotationSelectedIngredientsV1;if(selected&&Object.values(selected).some(v=>!strings(v)))throw Error('Invalid grocery selections');
 const identities=parsed.mealRotationGroupIdentitiesV1;if(identities&&(Object.values(identities).some(v=>typeof v!=='string'||!v)||new Set(Object.values(identities)).size!==Object.values(identities).length))throw Error('Invalid group identities');
 for(const key of ['mealRotationWeekdayColorsV1','mealRotationCategoryColorsV1'])if(parsed[key]&&Object.values(parsed[key]).some(v=>typeof v!=='string'||!/^#[0-9a-fA-F]{6}$/.test(v)))throw Error('Invalid saved colors: '+key);
 for(const key of ['mealRotationWeekdayMealOverridesV1'])if(parsed[key]&&Object.values(parsed[key]).some(v=>!id(v)))throw Error('Invalid saved meal choice');
 if(parsed.mealRotationWeekdayRecipeFiltersV1&&Object.values(parsed.mealRotationWeekdayRecipeFiltersV1).some(v=>!strings(v)))throw Error('Invalid legacy weekday filters');
 if(parsed.mealRotationTopCountsV1&&Object.values(parsed.mealRotationTopCountsV1).some(v=>!['number','string'].includes(typeof v)||!Number.isFinite(Number(v))))throw Error('Invalid group counts');
 if(parsed.mealRotationGroupDisplayOrderV1&&new Set(parsed.mealRotationGroupDisplayOrderV1).size!==parsed.mealRotationGroupDisplayOrderV1.length)throw Error('Invalid meal-group display order');
 for(const [key,fields]of [['mealRotationMakeAheadDisplayV1',['showMakeAheadReminders','showCompletedToday']],['mealRotationEditorSectionsV1',['ingredients','instructions']]])if(parsed[key]&&fields.some(field=>field in parsed[key]&&typeof parsed[key][field]!=='boolean'))throw Error('Invalid display preferences: '+key);
 const times=parsed.mealRotationTimeVisibilityV1;if(times&&['top','category','all'].some(view=>view in times&&(!object(times[view])||['cooking','marinate'].some(field=>field in times[view]&&typeof times[view][field]!=='boolean'))))throw Error('Invalid time display preferences');
 const expansion=parsed.mealRotationGroupSectionExpansionV1;if(expansion&&(expansion.version!==1||!object(expansion.groups)||Object.values(expansion.groups).some(v=>!object(v)||['rotation','ideas'].some(k=>k in v&&typeof v[k]!=='boolean'))))throw Error('Invalid group section expansion');
 const prefs=parsed.mealRotationRecipeViewPrefsV1;if(prefs){if('mode'in prefs&&!['full','split'].includes(prefs.mode))throw Error('Invalid recipe view mode');for(const k of ['ratio','landscapeRatio','timerAlarmVolume'])if(k in prefs&&!Number.isFinite(prefs[k]))throw Error('Invalid recipe view preference');for(const k of ['syncIngredients','autoCompleteIngredients','keepScreenAwake','autoOpenLinkedRecipes'])if(k in prefs&&typeof prefs[k]!=='boolean')throw Error('Invalid recipe view preference')}
 const fractions=parsed.mealRotationFractionMigrationBackupV2;if(fractions&&Object.values(fractions).some(v=>v!==null&&typeof v!=='string'))throw Error('Invalid fraction migration backup');
 if(Object.hasOwn(data,'mealRotationCookingSessionsV1'))validateCookingSessions(parsed.mealRotationCookingSessionsV1);
 if(Object.hasOwn(data,'mealRotationOccurrenceScalesV1'))validateOccurrenceScales(parsed.mealRotationOccurrenceScalesV1);
 if(Object.hasOwn(data,'mealRotationGroceryOccurrenceChecksV1'))validateGroceryOccurrenceChecks(parsed.mealRotationGroceryOccurrenceChecksV1);
 const timer=parsed.mealRotationCookingTimerV1;if(timer!==undefined&&timer!==null){if(!object(timer)||timer.version!==1||!['running','paused','complete'].includes(timer.status)||['id','recipeId','recipeName','stepToken','stepText'].some(k=>typeof timer[k]!=='string')||timer.status==='running'&&!Number.isFinite(timer.deadline)||timer.status==='paused'&&(!Number.isFinite(timer.remaining)||timer.remaining<=0))throw Error('Invalid cooking timer')}
 const history=parsed.mealRotationLastRotationBeforeV1;if(history!==undefined&&history!==null){if(!object(history)||!Array.isArray(history.meals)||!Array.isArray(history.mealPlans))throw Error('Invalid rotation history');validateBackupCore(startupCore({...history,mealPlans:{plans:history.mealPlans,...(typeof history.activePlanId==='string'?{activeId:history.activePlanId}:{})}}))}
 return parsed;
}
let bulkRecipeStorageDraft=null;const localStorage=bulkRecipeStorageBridge(mealBulkStorageBase);let cats=[],active='',menuCat=null,editId=null,showTop=true,checkedIngredients=new Set(),id=1,history=[],redoHistory=[];try{const savedChecks=JSON.parse(localStorage.getItem('mealRotationCheckedIngredientsV1')||'[]');if(Array.isArray(savedChecks))checkedIngredients=new Set(savedChecks)}catch(e){}// Cooking and marinating time visibility is independent in My Rotation and category pages.
// Version 2 backups capture every app-owned persistent key, including grocery selections.
// Preserve the original fields for compatibility with older backup readers.
function captureBackupStorage(){
 const data={};
 for(let i=0;i<localStorage.length;i++){
  const key=localStorage.key(i);
  if(key&&key.startsWith('mealRotation')&&!key.startsWith('mealRotationTestSandboxV1:')&&!key.startsWith('mealRotationTESTONLY__'))data[key]=localStorage.getItem(key);
 }
 return data;
}
// Validate the complete backup before changing any saved data.
function validateBackupCore(d){
 const weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
 const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
 if(!object(d)||!Array.isArray(d.cats)||d.cats.some(c=>typeof c!=='string'||!c.trim())||new Set(d.cats).size!==d.cats.length)throw new Error('Invalid groups');
 if(!Array.isArray(d.meals))throw new Error('Invalid recipes: recipe list is missing');const invalidRecipe=d.meals.find(m=>!object(m)||!Number.isSafeInteger(Number(m.id))||Number(m.id)<1||typeof m.name!=='string'||(m.cat!==''&&!d.cats.includes(m.cat))||('ingredients'in m&&!Array.isArray(m.ingredients))||('labels'in m&&(!Array.isArray(m.labels)||m.labels.some(x=>typeof x!=='string'))));if(invalidRecipe!==undefined)throw new Error('Invalid recipes: '+(object(invalidRecipe)?String(invalidRecipe.name||'unnamed recipe')+' (ID '+String(invalidRecipe.id??'missing')+')':'invalid recipe entry'));
 for(const m of d.meals){if('serveWith'in m&&(!Array.isArray(m.serveWith)||m.serveWith.some(v=>typeof v!=='string'||!v.trim())))throw Error('Invalid Serve with preferences');if('preferredSideGroupIds'in m&&(!Array.isArray(m.preferredSideGroupIds)||m.preferredSideGroupIds.some(id=>typeof id!=='string'||!id)))throw Error('Invalid preferred side groups');if('instructions'in m&&m.instructions!=null&&typeof m.instructions!=='string'&&(!Array.isArray(m.instructions)||m.instructions.some(b=>typeof b!=='string'&&(!b||typeof b!=='object'||!['step','section'].includes(b.type)||typeof b.text!=='string'))))throw Error('Invalid recipe instructions');if('notes'in m&&typeof m.notes!=='string')throw Error('Invalid recipe notes');}
 if(new Set(d.meals.map(m=>String(m.id))).size!==d.meals.length)throw new Error('Duplicate recipe IDs');
 if('active'in d&&typeof d.active!=='string')throw new Error('Invalid active group');
 if('mealPlans'in d){const plans=d.mealPlans;if(!object(plans)||!Array.isArray(plans.plans)||!plans.plans.length||plans.plans.some(p=>!object(p)||typeof p.id!=='string'||!p.id||typeof p.name!=='string'||!object(p.weekdayCategories)||('weekdayMealOverrides'in p&&!object(p.weekdayMealOverrides))||('weekdayRecipeFilters'in p&&!object(p.weekdayRecipeFilters))||('pinnedCats'in p&&!Array.isArray(p.pinnedCats)))||new Set(plans.plans.map(p=>p.id)).size!==plans.plans.length||('activeId'in plans&&!plans.plans.some(p=>p.id===plans.activeId)))throw new Error('Invalid meal plans');}
 if(d.mealPlans)for(const plan of d.mealPlans.plans)if('sideGroupPairs'in plan&&(!object(plan.sideGroupPairs)||Object.entries(plan.sideGroupPairs).some(([day,pairs])=>!weekdays.includes(day)||!object(pairs)||Object.values(pairs).some(id=>typeof id!=='string'||!id))))throw Error('Invalid side-group pairing');
 if(d.mealPlans)for(const plan of d.mealPlans.plans)if('dependentSideState'in plan&&(!object(plan.dependentSideState)||Object.entries(plan.dependentSideState).some(([key,value])=>{let parts;try{parts=JSON.parse(key)}catch(e){return true}return !Array.isArray(parts)||parts.length!==2||!weekdays.includes(parts[0])||typeof parts[1]!=='string'||!object(value)||typeof value.mainId!=='string'||typeof value.mealId!=='string'||typeof value.automatic!=='boolean'})))throw Error('Invalid dependent side state');
 if(d.mealPlans)for(const plan of d.mealPlans.plans)if('weekSchedule'in plan)validateWeekSchedule(plan.weekSchedule);
 if(d.mealPlans)for(const plan of d.mealPlans.plans)if('occasionalMeals'in plan&&(!object(plan.occasionalMeals)||Object.entries(plan.occasionalMeals).some(([day,id])=>!weekdays.includes(day)||!['string','number'].includes(typeof id)||!String(id).trim())))throw Error('Invalid one-time meals');
 for(const key of ['weekdayCategories','weekdayMealOverrides','weekdayColors','categoryColors','timeDisplayPrefs'])if(key in d&&!object(d[key]))throw new Error('Invalid '+key);
 for(const key of ['pinnedCats','expandedCats'])if(key in d&&(!Array.isArray(d[key])||d[key].some(x=>typeof x!=='string')))throw new Error('Invalid '+key);
}
function validateBackupStorage(data){
 if(!data||typeof data!=='object'||Array.isArray(data))throw Error('Invalid backup storage');
 if(Object.keys(data).some(key=>!key.startsWith('mealRotation')||key==='mealRotationRecoveryJournalV1'))throw Error('Invalid backup storage key');
 validateSavedRecords(data,true);
}
function normalizeImportedBackup(d){
 if(!d||typeof d!=='object'||Array.isArray(d))throw Error('Invalid backup');
 if(d.storage!==undefined&&(!d.storage||typeof d.storage!=='object'||Array.isArray(d.storage)))throw Error('Invalid backup storage');
 if('cats'in d||'meals'in d)validateBackupCore(startupCore(d));
 // Test-only records can be present in older exports. Never import them as app data.
 const cleaned={};
 for(const [key,value] of Object.entries(d.storage||{})){
  if(key==='mealRotationRecoveryJournalV1'||key.startsWith('mealRotationTestSandboxV1:')||key.startsWith('mealRotationTESTONLY__'))continue;
  cleaned[key]=value;
 }
 // The top-level recipe collection is authoritative for this backup format.
 if('cats'in d||'meals'in d)cleaned.mealRotationDataV1=JSON.stringify({cats:d.cats,active:d.active,meals:d.meals});
 if(d.mealPlans)cleaned.mealRotationPlansV1=JSON.stringify(d.mealPlans);
 if(d.weekdayCategories)cleaned.mealRotationWeekdayCategoriesV1=JSON.stringify(d.weekdayCategories);
 if(d.weekdayMealOverrides)cleaned.mealRotationWeekdayMealOverridesV1=JSON.stringify(d.weekdayMealOverrides);
 if(d.weekdayColors)cleaned.mealRotationWeekdayColorsV1=JSON.stringify(d.weekdayColors);
 if(d.categoryColors)cleaned.mealRotationCategoryColorsV1=JSON.stringify(d.categoryColors);
 if(d.pinnedCats)cleaned.mealRotationPinnedCategoriesV1=JSON.stringify(d.pinnedCats);
 if(d.expandedCats)cleaned.mealRotationExpandedCategoriesV1=JSON.stringify(d.expandedCats);
 if(typeof d.showMealPlanTabs==='boolean')cleaned.mealRotationShowPlanTabsV1=String(d.showMealPlanTabs);
 // Explicit top-level fields override storage; absent fields preserve storage verbatim.
 for(const [field,key]of Object.entries({cookSessions:'mealRotationCookingSessionsV1',checkedIngredients:'mealRotationCheckedIngredientsV1',timeDisplayPrefs:'mealRotationTimeVisibilityV1'}))if(Object.hasOwn(d,field))cleaned[key]=JSON.stringify(d[field]);
 for(const [field,key]of Object.entries({masterOpenMode:'mealRotationMasterOpenModeV1',masterPinsOverride:'mealRotationMasterPinsOverrideV1',autoPinTopCategories:'mealRotationAutoPinTopCategoriesV1',applyPinsToAllTabs:'mealRotationApplyPinsAllTabsV1'}))if(Object.hasOwn(d,field))cleaned[key]=String(d[field]);
 return cleaned;
}
function restoreBackupStorage(data,operation=null){
 validateBackupStorage(data);
 const descriptor=operation||{id:'backup-restore',kind:'backup-restore',ownerId:null};
 try{const result=mealPersistence.transaction(()=>restoreBackupStorageWrites(data));mealPersistence.resolve(descriptor.id);return result}
 catch(error){mealPersistence.offerRetry(operation?.retry||(()=>{restoreBackupStorage(data);mealPersistence.reload()}),{...descriptor,proposal:data});throw error}
}
function restoreBackupStorageWrites(data){
 if(!data||typeof data!=='object'||Array.isArray(data))throw new Error('Invalid backup storage');
 const entries=Object.entries(data);
 if(!entries.length||entries.some(([key,value])=>!key.startsWith('mealRotation')||typeof value!=='string'))throw new Error('Invalid backup storage');
 validateBackupStorage(data);
 // Never delete the existing records before the replacement has been written.
 // A persistent storage failure may prevent rollback, so preserve the original
 // recipe data until every other replacement has succeeded.
 const before=captureBackupStorage();
 const primary='mealRotationDataV1';
 const changed=[];
 try{
  for(const [key,value] of entries){
   if(key===primary||before[key]===value)continue;
   localStorage.setItem(key,value);
   changed.push(key);
  }
  // Commit the main recipe record last, after all other writes succeed.
  if(before[primary]!==data[primary]){
   localStorage.setItem(primary,data[primary]);
   changed.push(primary);
  }
  // Remove obsolete keys only after all replacement writes succeed.
  for(const key of Object.keys(before))if(!(key in data)){
   localStorage.removeItem(key);
   changed.push(key);
  }
 }catch(error){
  const rollbackFailures=[];
  for(const key of changed.reverse()){
   try{
    if(Object.prototype.hasOwnProperty.call(before,key))localStorage.setItem(key,before[key]);
    else localStorage.removeItem(key);
   }catch(e){rollbackFailures.push(key)}
  }
  if(rollbackFailures.length)throw new Error('Restore failed; some settings could not be rolled back ('+rollbackFailures.join(', ')+'). Your original backup file is unchanged. '+error.message);
  throw error;
 }
}

// Recipe content remains on existing meal records; cooking progress is separate.
const COOKING_SESSIONS_KEY='mealRotationCookingSessionsV1';
let cookingSessions={version:1,occurrences:{}},cookingStorageInvalid=false;
try{const saved=localStorage.getItem(COOKING_SESSIONS_KEY);if(saved){const parsed=JSON.parse(saved);validateCookingSessions(parsed);cookingSessions=parsed}}catch(e){cookingStorageInvalid=true}
function validateCookingSessions(value){
 const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
 if(!obj(value)||value.version!==1||!obj(value.occurrences))throw Error('Invalid cooking progress');
 for(const [key,s] of Object.entries(value.occurrences)){
  if(!obj(s)||typeof s.id!=='string'||!s.id||!obj(s.context)||!['planId','day','cat','mealId','parentId'].every(k=>typeof s.context[k]==='string')||
   !['ingredients','steps'].every(k=>Array.isArray(s[k])&&s[k].every(v=>typeof v==='string'))||key!==cookingOccurrenceKey(s.context))throw Error('Invalid cooking occurrence');
  if(s.autoIngredients!==undefined&&(!Array.isArray(s.autoIngredients)||!s.autoIngredients.every(t=>typeof t==='string')))throw Error('Invalid automatic ingredient progress');
  if(s.ingredientOverrides!==undefined&&(!obj(s.ingredientOverrides)||!Object.values(s.ingredientOverrides).every(v=>typeof v==='boolean')))throw Error('Invalid manual ingredient choices');
 }
}
function writeCookingSessions(next){
 if(cookingStorageInvalid){showAppMessage('Saved cooking progress could not be read. Export a backup before repairing this browser’s saved data.');return false}
 try{localStorage.setItem(COOKING_SESSIONS_KEY,JSON.stringify(next));cookingSessions=next;return true}
 catch(e){showAppMessage('Cooking progress could not be saved. Your browser may be low on storage. Existing recipes and saved progress have not been replaced.');return false}
}
function cookingOccurrenceKey(c){return JSON.stringify([c.planId,c.day,c.mealId,c.parentId||''])}
function cookingContext(planId,day,cat,meal,parentId=''){return {planId:String(planId),day:String(day),cat:String(cat),mealId:String(meal.id),parentId:parentId==null?'':String(parentId)}}
function cookingSession(context,create=false){
 if(!context)return null;const key=cookingOccurrenceKey(context);if(cookingSessions.occurrences[key])return cookingSessions.occurrences[key];
 if(!create)return null;
 const next=JSON.parse(JSON.stringify(cookingSessions));
 next.occurrences[key]={id:typeof crypto.randomUUID==='function'?crypto.randomUUID():'cook-'+Date.now()+'-'+Math.random().toString(36).slice(2),context:{...context},ingredients:[],steps:[]};
 return writeCookingSessions(next)?cookingSessions.occurrences[key]:null;
}
// Materialized ingredients remain compatible with older backups. Explicit choices win.
function prepareIngredientChoices(session){
 if(!session.autoIngredients)session.autoIngredients=[];
 if(!session.ingredientOverrides)session.ingredientOverrides=Object.fromEntries(session.ingredients.filter(t=>!session.autoIngredients.includes(t)).map(t=>[t,true]));
}
function materializeIngredientChoices(session){
 const manual=session.ingredientOverrides||{},automatic=session.autoIngredients||[];
 session.ingredients=[...new Set([...Object.entries(manual).filter(([,done])=>done).map(([token])=>token),...automatic.filter(token=>manual[token]!==false)])];
}
function updateAutomaticCookingIngredients(session,meal,newlyCompletedStep=null){
 prepareIngredientChoices(session);
 const matches=recipeIngredientMatches(meal),requirements=new Map();
 // Repeated indistinguishable steps cannot safely establish that an ingredient is finished.
 const steps=cookingItemTokens(meal).steps.filter(s=>s.type==='step'&&cleanInstructionBlock(s).type==='step');
 if(steps.every(s=>matches.has(s.token)))for(const [step,ingredients] of matches)for(const ingredient of ingredients){if(!requirements.has(ingredient))requirements.set(ingredient,[]);requirements.get(ingredient).push(step)}
 const candidates=new Set(session.autoIngredients);
 for(const step of Array.isArray(newlyCompletedStep)?newlyCompletedStep:[newlyCompletedStep])for(const token of matches.get(step)||[])candidates.add(token);
 session.autoIngredients=[...candidates].filter(token=>requirements.has(token)&&requirements.get(token).every(step=>session.steps.includes(step)));
 materializeIngredientChoices(session);
}

const OCCURRENCE_SCALES_KEY='mealRotationOccurrenceScalesV1',RECIPE_SCALES=[.5,1,1.5,2,3];
let occurrenceScales={version:1,occurrences:{}},scaleStorageInvalid=false;
function validateOccurrenceScales(value){
 if(!value||value.version!==1||!value.occurrences||typeof value.occurrences!=='object'||Array.isArray(value.occurrences))throw Error('Invalid recipe scaling');
 for(const [key,entry] of Object.entries(value.occurrences))if(!entry||!validRecipeMultiplier(entry.multiplier)||!entry.context||entry.context.scaleGroupId!==undefined&&typeof entry.context.scaleGroupId!=='string'||!['planId','day','cat','mealId','parentId'].every(k=>typeof entry.context[k]==='string')||(key!==cookingOccurrenceKey(entry.context)&&key!==scaleOccurrenceKey(entry.context)))throw Error('Invalid recipe scale occurrence');
}
try{const raw=localStorage.getItem(OCCURRENCE_SCALES_KEY);if(raw){const parsed=JSON.parse(raw);validateOccurrenceScales(parsed);occurrenceScales=parsed}}catch(e){scaleStorageInvalid=true}
function writeOccurrenceScales(next){
 if(scaleStorageInvalid){showAppMessage('Saved recipe multipliers could not be read. Export a backup before repairing this browser’s data.');return false}
 try{localStorage.setItem(OCCURRENCE_SCALES_KEY,JSON.stringify(next));occurrenceScales=next;return true}catch(e){showAppMessage('The recipe multiplier could not be saved. Existing data has been kept.');return false}
}
function validRecipeMultiplier(value){return typeof value==='number'&&Number.isFinite(value)&&value>0}
// Keep cooking-progress identities unchanged. Scales distinguish independent group slots.
function scaleOccurrenceKey(c){return JSON.stringify([...JSON.parse(cookingOccurrenceKey(c)),c.scaleGroupId||groupIdentity(c.cat)||c.cat])}
function occurrenceMultiplier(context){
 if(!context)return 1;
 const exact=occurrenceScales.occurrences[scaleOccurrenceKey(context)];if(exact)return exact.multiplier;
 const legacy=occurrenceScales.occurrences[cookingOccurrenceKey(context)];
 // Old saves describe one group, never all copies of a recipe on that day.
 return legacy&&legacy.context.cat===context.cat?legacy.multiplier:1;
}
function clearOccurrenceScales(predicate){const next=JSON.parse(JSON.stringify(occurrenceScales));let changed=false;for(const [key,entry] of Object.entries(next.occurrences))if(predicate(entry.context)){delete next.occurrences[key];changed=true}if(changed)writeOccurrenceScales(next)}
function setViewedRecipeScale(value){
 const view=recipeViewer;if(!view||!validRecipeMultiplier(value))return false;
 if(view.context){
  if(groceryCheckStorageInvalid){showAppMessage('Saved grocery checks could not be read. No multiplier was changed.');return false}
  if(!definiteRecipeContext(view.context))return false;
  const before=captureGroceryCheckStates(),next=JSON.parse(JSON.stringify(occurrenceScales)),context={...view.context,scaleGroupId:groupIdentity(view.context.cat,true)||view.context.cat},key=scaleOccurrenceKey(context);
  const legacy=cookingOccurrenceKey(context);if(next.occurrences[legacy]?.context.cat===context.cat)delete next.occurrences[legacy];
  if(value===1)delete next.occurrences[key];else next.occurrences[key]={context,multiplier:value};
  if(!writeOccurrenceScales(next)){renderRecipeViewer();return false}
  preserveGroceryCheckStates(before);groceryOccurrenceChecks.quantities??={};
  for(const source of getGroceryContributions(true)){
   const prior=before.get(source.id);if(!prior||!source.quantity||!prior.source.quantity)continue;
   const checked=prior.amount|| (prior.checked?prior.source.quantity:{lo:0,hi:0});
   groceryOccurrenceChecks.quantities[source.id]={lo:Math.min(checked.lo,source.quantity.lo),hi:Math.min(checked.hi,source.quantity.hi)};
  }
  saveGroceryOccurrenceChecks();view.contentChanged=true;
 }else view.previewScale=value;
 renderRecipeViewer();return true;
}
const recipeFractionValues={'¼':.25,'½':.5,'¾':.75,'⅓':1/3,'⅔':2/3,'⅛':.125,'⅜':.375,'⅝':.625,'⅞':.875};
const recipeAllFractionValues={...recipeFractionValues,'⅐':1/7,'⅑':1/9,'⅒':.1,'⅕':.2,'⅖':.4,'⅗':.6,'⅘':.8,'⅙':1/6,'⅚':5/6};
function recipeQuantityNumber(text){
 const clean=String(text).replace(/\u2044/g,'/').replace(/[¼½¾⅓⅔⅛⅜⅝⅞⅐⅑⅒⅕⅖⅗⅘⅙⅚]/g,c=>' '+Object.entries(recipeAllFractionValues).find(([k])=>k===c)[1]).trim();
 const parts=clean.split(/\s+/);let sum=0;for(const part of parts){if(part.includes('/')){const [n,d]=part.split('/').map(Number);if(!Number.isFinite(n)||!Number.isFinite(d)||d===0)return null;sum+=n/d}else{if(!/^\d*(?:\.\d+)?$/.test(part)&&!/^\d+$/.test(part))return null;sum+=Number(part)}}return Number.isFinite(sum)?sum:null;
}
function formatRecipeQuantity(value){
 const rounded=Math.round(value*1e6)/1e6,whole=Math.floor(value+1e-9),fraction=value-whole;
 if(Math.abs(fraction)<1e-8)return String(whole);
 for(const [glyph,amount] of Object.entries(recipeFractionValues))if(Math.abs(fraction-amount)<1e-8)return (whole?String(whole):'')+glyph;
 for(const d of [16]){const n=Math.round(fraction*d);if(n&&Math.abs(fraction-n/d)<1e-8)return (whole?whole+' ':'')+n+'/'+d}
 return String(rounded);
}
function parseRecipeQuantity(line){
 const number='(?:\\d+\\s+\\d+[/⁄]\\d+|\\d+[¼½¾⅓⅔⅛⅜⅝⅞⅐⅑⅒⅕⅖⅗⅘⅙⅚]|\\d+[/⁄]\\d+|\\d*\\.\\d+|\\d+|[¼½¾⅓⅔⅛⅜⅝⅞⅐⅑⅒⅕⅖⅗⅘⅙⅚])';
 const match=String(line).match(new RegExp('^(\\s*)('+number+')(?:\\s*(?:[-–—]|to)\\s*('+number+'))?\\s+(.+)$','i'));if(!match)return null;
 const lo=recipeQuantityNumber(match[2]),hi=match[3]?recipeQuantityNumber(match[3]):lo,rest=match[4];
 if(lo===null||hi===null||hi<lo||/^(?:[x×/]|\d)/i.test(rest)||/(?:\b(?:and|or|plus)\b|\+)\s*\d/.test(rest))return null;
 return {lo,hi,rest,leading:match[1]};
}
function scaleRecipeIngredient(line,multiplier){
 if(multiplier===1||syncIngredientHeading(line))return String(line);
 const quantity=parseRecipeQuantity(line);if(!quantity||!Number.isFinite(quantity.lo*multiplier)||!Number.isFinite(quantity.hi*multiplier))return String(line);
 return quantity.leading+formatRecipeQuantity(quantity.lo*multiplier)+(quantity.hi!==quantity.lo?'–'+formatRecipeQuantity(quantity.hi*multiplier):'')+' '+quantity.rest;
}
const groceryQuantityUnits={cup:'cup',cups:'cup',tbsp:'tbsp',tablespoon:'tbsp',tablespoons:'tbsp',tsp:'tsp',teaspoon:'tsp',teaspoons:'tsp',g:'g',gram:'g',grams:'g',kg:'kg',oz:'oz',ounce:'oz',ounces:'oz',lb:'lb',lbs:'lb',pound:'lb',pounds:'lb',ml:'ml',l:'l',liter:'l',litre:'l',clove:'clove',cloves:'clove',piece:'piece',pieces:'piece',sprig:'sprig',sprigs:'sprig'};
function groceryQuantityParts(line){
 const quantity=parseRecipeQuantity(line);if(!quantity)return null;
 const unitMatch=quantity.rest.match(/^([a-z]+)\.?\s+(.+)$/i),unit=unitMatch?groceryQuantityUnits[unitMatch[1].toLowerCase()]||'':'';
 const name=unit?unitMatch[2]:quantity.rest;
 return {...quantity,unit,name,key:'quantity:'+JSON.stringify([unit,name.normalize('NFKC').toLowerCase().replace(/[a-z]+/g,w=>syncIngredientWords(w).join(' ')).replace(/\s+/g,' ').trim()])};
}
// Optional per-occurrence check states supplement legacy ingredient/quantity keys.
// Membership and recipe ingredients continue to use their existing saved records.
const GROCERY_OCCURRENCE_CHECKS_KEY='mealRotationGroceryOccurrenceChecksV1';
let groceryOccurrenceChecks={version:1,checks:{}},groceryCheckStorageInvalid=false;
function validateGroceryOccurrenceChecks(value){
 if(!value||value.version!==1||!value.checks||typeof value.checks!=='object'||Array.isArray(value.checks)||value.quantities!==undefined&&(!value.quantities||typeof value.quantities!=='object'||Array.isArray(value.quantities)))throw Error('Invalid grocery occurrence checks');
 for(const amount of Object.values(value.quantities||{}))if(!amount||!Number.isFinite(amount.lo)||!Number.isFinite(amount.hi)||amount.lo<0||amount.hi<amount.lo)throw Error('Invalid checked grocery quantity');
 for(const [key,checked] of Object.entries(value.checks)){
  let source;try{source=JSON.parse(key)}catch(e){throw Error('Invalid grocery source')}
  if(!Array.isArray(source)||source.length!==3||typeof source[0]!=='string'||typeof source[1]!=='string'||!Number.isSafeInteger(source[2])||source[2]<0||typeof checked!=='boolean')throw Error('Invalid grocery source check');
  let occurrence;try{occurrence=JSON.parse(source[0])}catch(e){throw Error('Invalid grocery occurrence')}
  if(!Array.isArray(occurrence)||![4,5,6].includes(occurrence.length)||occurrence.some(value=>typeof value!=='string'))throw Error('Invalid grocery occurrence');
 }
}
try{const raw=localStorage.getItem(GROCERY_OCCURRENCE_CHECKS_KEY);if(raw){const value=JSON.parse(raw);validateGroceryOccurrenceChecks(value);groceryOccurrenceChecks=value}}catch(e){groceryCheckStorageInvalid=true}
function saveGroceryOccurrenceChecks(){
 if(groceryCheckStorageInvalid)return false;
 try{localStorage.setItem(GROCERY_OCCURRENCE_CHECKS_KEY,JSON.stringify(groceryOccurrenceChecks));return true}catch(e){return false}
}
function groceryOccurrenceIdentity(plan,entry){
 const slot=rotationGroupScheduled(plan,entry.day,entry.cat);
 return JSON.stringify([String(plan.id),entry.day,String(entry.meal.id),(slot||entry.occasional&&!(entry.linkedTo??entry.parentId))?'slot':'linked:'+String(entry.linkedTo??entry.parentId??''),cats.includes(entry.cat)?groupIdentity(entry.cat,true):String(entry.cat||'@day')]);
}
function groceryStoredAmount(source,ledger){
 for(const key of [source.id,...(source.legacyOwner===false?[]:source.legacyIds||[source.legacyId])]){if(ledger.quantities?.[key])return ledger.quantities[key];if(typeof ledger.checks?.[key]==='boolean')return null}return null;
}
function groceryCheckedAmount(source,ledger=groceryOccurrenceChecks,legacy=checkedIngredients){
 const saved=groceryStoredAmount(source,ledger);if(saved&&source.quantity)return {lo:Math.min(saved.lo,source.quantity.lo),hi:Math.min(saved.hi,source.quantity.hi)};
 return source.quantity&&(grocerySourceChecked(source,ledger,legacy)?{lo:source.quantity.lo,hi:source.quantity.hi}:{lo:0,hi:0});
}
function grocerySourceChecked(source,ledger=groceryOccurrenceChecks,legacy=checkedIngredients){
 if(typeof source.segmentChecked==='boolean')return source.segmentChecked;
 const amount=groceryStoredAmount(source,ledger);if(amount&&source.quantity)return amount.lo>=source.quantity.lo-1e-8&&amount.hi>=source.quantity.hi-1e-8;
 const stored=ledger?.checks?.[source.id];
 if(typeof stored==='boolean')return stored;if(source.legacyOwner===false)return false;const old=(source.legacyIds||[source.legacyId]).map(key=>ledger.checks[key]).find(value=>typeof value==='boolean');return typeof old==='boolean'?old:legacy.has(source.baseKey)||source.checkKeys.some(key=>legacy.has(key));
}
function captureGroceryCheckStates(includeUpcoming=false){return new Map(getGroceryContributions(true,includeUpcoming?'both':'rotation').map(source=>[source.id,{source,checked:grocerySourceChecked(source),amount:groceryCheckedAmount(source)}]))}
function preserveGroceryCheckStates(states){for(const [id,item] of states){groceryOccurrenceChecks.checks[id]=item.checked;if(item.amount)(groceryOccurrenceChecks.quantities??={})[id]={...item.amount}}}
function groceryItemChecked(key,item){
 if(item.contributions)return item.contributions.every(source=>grocerySourceChecked(source));
 return checkedIngredients.has(key)||(item.checkGroups?.length?item.checkGroups.every(group=>group.some(k=>checkedIngredients.has(k))):!!item.checkKeys?.length&&item.checkKeys.every(k=>checkedIngredients.has(k)));
}
function setGroceryItemChecked(key,item,checked){
 if(item.contributions){
  // Materialize legacy states before changing a global key shared with other rows.
  const states=captureGroceryCheckStates(true);preserveGroceryCheckStates(states);
  for(const source of item.contributions){
   groceryOccurrenceChecks.checks[source.id]=checked;
   if(source.quantity){const full=states.get(source.id)?.source,prior=states.get(source.id)?.amount||{lo:0,hi:0},q=source.quantity;
    (groceryOccurrenceChecks.quantities??={})[source.id]=source.segmentChecked===undefined?{lo:checked?q.lo:0,hi:checked?q.hi:0}:{lo:Math.max(0,Math.min(full.quantity.lo,prior.lo+(checked?1:-1)*q.lo)),hi:Math.max(0,Math.min(full.quantity.hi,prior.hi+(checked?1:-1)*q.hi))};
   }
  }
  const all=[...states.values()].map(item=>item.source).filter(source=>source.baseKey===item.baseKey);
  if(all.every(source=>grocerySourceChecked(source)))checkedIngredients.add(item.baseKey);else checkedIngredients.delete(item.baseKey);
  if(!checked){checkedIngredients.delete(key);for(const old of item.checkKeys||[])checkedIngredients.delete(old)}
  saveGroceryOccurrenceChecks();return;
 }
 if(checked)checkedIngredients.add(key);else{checkedIngredients.delete(key);for(const old of item.checkKeys||[])checkedIngredients.delete(old)}
}
function reconcileRotatedGroceryChecks(before,affected,restore=null){
 if(hasDependentSideSlots()){coordinateDependentSides(!!restore);saveActiveMealPlan();}
 const reset=new Set(affected.map(item=>{const plan=mealPlans.find(plan=>plan.id===item.planId);return plan?groceryOccurrenceIdentity(plan,{...item,meal:item.meal||{id:item.mealId},linkedTo:item.linkedTo??item.parentId}):''}));
 const restoredLegacy=restore?new Set(restore.checkedIngredients||[]):null;
 const savedLedger=groceryOccurrenceChecks,next={version:1,checks:{},quantities:{}};for(const [id,checked]of Object.entries(savedLedger.checks)){const occurrence=JSON.parse(JSON.parse(id)[0]);if(occurrence.length===6&&occurrence[5]>=cookingLocalDate(new Date())&&meals.some(meal=>String(meal.id)===occurrence[2])&&mealPlans.some(plan=>String(plan.id)===occurrence[0])){next.checks[id]=checked;if(savedLedger.quantities?.[id])next.quantities[id]={...savedLedger.quantities[id]}}}const currentSources=getGroceryContributions(true),visible=new Set(currentSources.map(source=>source.id));
 for(const plan of mealPlans)if(plan.weekSchedule?.linkedGroceryChecks)for(const id of Object.keys(plan.weekSchedule.linkedGroceryChecks)){const occurrence=JSON.parse(JSON.parse(id)[0]);if(affected.some(item=>item.planId===plan.id&&item.day===occurrence[1]&&(item.meal?.linkedMealIds||[]).some(side=>String(side)===occurrence[2]))){delete plan.weekSchedule.linkedGroceryChecks[id];delete plan.weekSchedule.linkedGroceryQuantities?.[id]}}
 for(const [id,item]of before){const source=item.source;if(visible.has(id)||!source?.parentId||[...reset].some(key=>{if(!key)return false;const parts=JSON.parse(key);return parts[0]===String(source.planId)&&parts[1]===source.day&&parts[2]===source.parentId}))continue;const plan=mealPlans.find(p=>p.id===source.planId);if(plan&&getDisplayedWeekdayMealsForPlan(plan).some(entry=>entry.day===source.day&&String(entry.meal.id)===source.parentId)){const state=editableWeekSchedule(plan);state.linkedGroceryChecks={...state.linkedGroceryChecks,[id]:item.checked};if(item.amount)state.linkedGroceryQuantities={...state.linkedGroceryQuantities,[id]:{...item.amount}}}}
 for(const source of currentSources){
  const was=before.get(source.id)||(source.legacyOwner?before.get(source.legacyId):null);
  const incoming=!before.has(source.id)&&typeof savedLedger.checks[source.id]==='boolean';
  if(incoming&&!restore)next.checks[source.id]=savedLedger.checks[source.id];
  else if(restore&&reset.has(source.occurrence))next.checks[source.id]=grocerySourceChecked(source,restore.groceryOccurrenceChecks||{version:1,checks:{}},restoredLegacy);
  else next.checks[source.id]=!reset.has(source.occurrence)&&was?was.checked:false;
  const amount=incoming&&!restore?savedLedger.quantities?.[source.id]:restore&&reset.has(source.occurrence)?restore.groceryOccurrenceChecks?.quantities?.[source.id]:!reset.has(source.occurrence)&&was?.amount;
  if(amount&&source.quantity)next.quantities[source.id]={lo:Math.min(amount.lo,source.quantity.lo),hi:Math.min(amount.hi,source.quantity.hi)};
 }
 groceryOccurrenceChecks=next;saveGroceryOccurrenceChecks();saveActiveMealPlan();
}
function renameGrocerySourceChecks(meal,from,to){
 const oldKey=ingredientKey(compactIngredientFractions(from)),newKey=ingredientKey(compactIngredientFractions(to));
 for(const [id,checked] of Object.entries(groceryOccurrenceChecks.checks)){
  const source=JSON.parse(id),occurrence=JSON.parse(source[0]);
  if(occurrence[2]===String(meal.id)&&source[1]===oldKey){const key=JSON.stringify([source[0],newKey,source[2]]);groceryOccurrenceChecks.checks[key]=checked;const amount=groceryOccurrenceChecks.quantities?.[id];if(amount)(groceryOccurrenceChecks.quantities??={})[key]={...amount}}
 }
}
function uncheckGrocerySourceLines(meal,lines){
 const keys=new Set(lines.map(ingredientKey)),ids=new Set(mealLinkedCopies(meal).map(m=>String(m.id)));
 for(const source of getGroceryContributions(true))if(ids.has(String(source.mealId))&&keys.has(ingredientKey(source.original))){groceryOccurrenceChecks.checks[source.id]=false;delete groceryOccurrenceChecks.quantities?.[source.id]}
}

function normalizeRecipeText(value){
 if(value===undefined||value===null)return '';
 const text=String(value);if(!/<\/?[a-z][^>]*>/i.test(text))return text.trim();
 const doc=new DOMParser().parseFromString(text,'text/html');doc.querySelectorAll('script,style,iframe,object').forEach(e=>e.remove());
 doc.querySelectorAll('br').forEach(e=>e.replaceWith('\n'));doc.querySelectorAll('p,div,li,h1,h2,h3,h4,h5,h6').forEach(e=>e.append('\n'));
 return doc.body.textContent.replace(/\n[ \t]+/g,'\n').replace(/\n{3,}/g,'\n\n').trim();
}
function instructionBlocks(value){
 const result=[];
 const add=(type,text)=>{text=normalizeRecipeText(text);if(text)result.push({type,text})};
 function visit(x,depth=0){
  if(depth>30||x==null)return;if(Array.isArray(x)){x.forEach(v=>visit(v,depth+1));return}
  if(typeof x==='string'){
   if(/<(?:ol|ul|li|h[1-6]|p|div)\b/i.test(x)){
    const doc=new DOMParser().parseFromString(x,'text/html');doc.querySelectorAll('script,style,iframe,object').forEach(e=>e.remove());
    const walk=node=>{if(node.nodeType===3){if(node.textContent.trim())add('step',node.textContent);return}if(node.nodeType!==1)return;
     if(/^H[1-6]$/.test(node.tagName)){add('section',node.textContent);return}
     if(node.tagName==='LI'||node.tagName==='P'){add('step',node.innerHTML);return}
     [...node.childNodes].forEach(walk)};
    [...doc.body.childNodes].forEach(walk);return;
   }
   x.split(/\r?\n/).forEach(line=>{const t=line.trim();if(!t)return;const heading=t.match(/^#{1,6}\s+(.+)$/)||t.match(/^\*\*(.+?)\*\*:?$/);add(heading||(/^[^\n]{1,100}:$/.test(t)&&!/^\d+[.)]/.test(t))?'section':'step',heading?heading[1]:t)});return;
  }
  if(typeof x!=='object')return;
  const type=String(x['@type']||x.type||'').toLowerCase();
  if(type.includes('section')||Array.isArray(x.itemListElement)||Array.isArray(x.steps)){
   add('section',x.name||x.title||(type==='section'?x.text:''));visit(x.itemListElement||x.steps,depth+1);
  }else add(type==='heading'?'section':'step',x.name&&x.text&&normalizeRecipeText(x.name)!==normalizeRecipeText(x.text)?normalizeRecipeText(x.name)+'\n'+normalizeRecipeText(x.text):x.text??x.description??x.name??'');
 }
 visit(value);return result;
}
function instructionEditorText(value){return instructionBlocks(value).map(b=>b.type==='section'?'## '+b.text:b.text).join('\n\n')}
function cookingItemTokens(meal){
 const normalize=x=>String(x).normalize('NFKC').replace(/\u2044/g,'/').replace(/\s+/g,' ').trim();
 const counts=new Map();const token=(kind,text,section='')=>{const stableText=kind==='step'?normalize(text).replace(/^(?:step\s*\d+[:.)]?|\d+[.)])\s+/i,''):normalize(ingredientLine(text));const base=JSON.stringify([kind,section,stableText]);const n=counts.get(base)||0;counts.set(base,n+1);return base+'#'+n};
 const ingredients=(Array.isArray(meal.ingredients)?meal.ingredients:[]).map(text=>({text:String(text),token:token('ingredient',text)}));
 let section='';const steps=instructionBlocks(meal.instructions).map(b=>{if(b.type==='section'){section=normalize(b.text);return {...b}}return {...b,token:token('step',b.text,section)}});
 return {ingredients,steps};
}
function reconcileCookingItems(oldMeal,newMeal){
 const old=cookingItemTokens(oldMeal),next=cookingItemTokens(newMeal);
 const ingredientChanged=JSON.stringify(oldMeal.ingredients)!==JSON.stringify(newMeal.ingredients),stepChanged=JSON.stringify(instructionBlocks(oldMeal.instructions))!==JSON.stringify(instructionBlocks(newMeal.instructions));
 const allowed=(items,changed)=>{const counts=new Map();for(const x of items)if(x.token){const base=x.token.slice(0,x.token.lastIndexOf('#'));counts.set(base,(counts.get(base)||0)+1)}return new Set(items.filter(x=>x.token&&(!changed||counts.get(x.token.slice(0,x.token.lastIndexOf('#')))===1)).map(x=>x.token))};
 const ing=allowed(next.ingredients,ingredientChanged),steps=allowed(next.steps,stepChanged);let dirty=false;const copy=JSON.parse(JSON.stringify(cookingSessions));
 for(const entry of Object.values(copy.occurrences))if(entry.context.mealId===String(newMeal.id)){
  const before=JSON.stringify(entry);
  const a=entry.ingredients.filter(k=>ing.has(k)),b=entry.steps.filter(k=>steps.has(k));if(a.length!==entry.ingredients.length||b.length!==entry.steps.length){entry.ingredients=a;entry.steps=b;dirty=true}
  if(entry.autoIngredients||entry.ingredientOverrides){entry.autoIngredients=(entry.autoIngredients||[]).filter(t=>ing.has(t));if(entry.ingredientOverrides)entry.ingredientOverrides=Object.fromEntries(Object.entries(entry.ingredientOverrides).filter(([t])=>ing.has(t)));if(ingredientChanged||stepChanged)updateAutomaticCookingIngredients(entry,newMeal);if(JSON.stringify(entry)!==before)dirty=true}
 }
 if(dirty)writeCookingSessions(copy);
}
function resetCookingContexts(predicate){
 const next=JSON.parse(JSON.stringify(cookingSessions));let dirty=false;
 for(const [key,s] of Object.entries(next.occurrences))if(predicate(s.context)){delete next.occurrences[key];dirty=true}
 if(dirty)writeCookingSessions(next);
}
// Compare real recipe/group/plan changes, never view changes (including hiding tabs).
let cookingScheduleSignature='';
function reconcileCookingSchedule(){
 const signature=JSON.stringify([meals.map(m=>[m.id,m.cat,m.rotation,m.linkGroup,m.linkedMealIds,m.labels]),cats,mealPlans.map(p=>[p.id,p.weekdayCategories,p.weekdayMealOverrides,p.weekdayRecipeFilters,p.weekSchedule]),activePlanId,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters]);
 if(signature===cookingScheduleSignature)return;cookingScheduleSignature=signature;
 const valid=new Set(),validScales=new Set(),visible=showMealPlanTabs;
 try{for(const mode of [true,false]){showMealPlanTabs=mode;for(const plan of mealPlans){const current=plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan;
  const entries=getDisplayedWeekdayMealsForPlan(current).concat(hiddenWeekEntries(current));for(const {day,cat,meal,linkedTo} of entries){valid.add(cookingOccurrenceKey(cookingContext(plan.id,day,cat,meal,linkedTo)));validScales.add(scaleOccurrenceKey(cookingContext(plan.id,day,cat,meal,linkedTo)));
   for(const linkedId of meal.linkedMealIds||[]){const child=meals.find(m=>String(m.id)===String(linkedId));if(child){valid.add(cookingOccurrenceKey(cookingContext(plan.id,day,child.cat,child,meal.id)));validScales.add(scaleOccurrenceKey(cookingContext(plan.id,day,child.cat,child,meal.id)))}}
  }
 }}}finally{showMealPlanTabs=visible}
 resetCookingContexts(c=>!valid.has(cookingOccurrenceKey(c)));clearOccurrenceScales(c=>!validScales.has(scaleOccurrenceKey(c)));
}

// Presentation cleanup leaves stored source text and progress tokens intact.
function cleanInstructionText(value){
 let text=normalizeRecipeText(value).replace(/&(?:nbsp|amp|lt|gt|quot|#39);/g,s=>({'&nbsp;':' ','&amp;':'&','&lt;':'<','&gt;':'>','&quot;':'"','&#39;':"'"}[s]));
 text=text.replace(/\*\*|__/g,'').replace(/^\s*(?:[•●▪◦]|[-*]\s+)\s*/,'');
 // Only explicit list syntax is removed: bare temperatures, quantities and durations survive.
 text=text.replace(/^\s*step\s+\d+\s*[:.)-]?\s*/i,'').replace(/^\s*\d+\s*[.)]\s*(?=[A-Za-z])/,'');
 return text.trim();
}
function cleanInstructionBlock(block){
 const raw=String(block.text||'');
 const numberedBold=raw.match(/^\s*\*\*\d+\*\*\s*(.*)$/s);
 const text=cleanInstructionText(numberedBold?numberedBold[1]:raw);
 // Conservatively recognize short, title-cased headings from malformed Markdown exports.
 const heading=numberedBold&&text.length<80&&!/[.!?]$/.test(text)&&/^(?:[A-Z][a-z]+)(?:\s+(?:[A-Z][a-z]+|the|and|for|of|to|a|an)){1,8}:?$/.test(text);
 return {...block,text,type:heading?'section':block.type};
}