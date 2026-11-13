// Run with `node tests/vanilla_storage_backup.test.js`. No packages or build step.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const state=fs.readFileSync('state.js','utf8');
const imports=fs.readFileSync('import-export.js','utf8');
const journalKey='mealRotationRecoveryJournalV1';
const persistence=state.slice(state.indexOf('function createMealPersistence('),state.indexOf('\nconst mealPersistence='))
 .replace('return {storage,inspect,','return {testWriteJournal:writeJournal,testReplace:replace,storage,inspect,');
function environment(initial={}){
 const records=new Map(Object.entries(initial)),writes=[];
 let fail=()=>false,reloads=0;
 const base={
  get length(){return records.size},key:i=>[...records.keys()][i]??null,
  getItem:k=>records.get(k)??null,
  setItem(k,v){writes.push(k);if(fail(k))throw Object.assign(Error('Full'),{name:'QuotaExceededError'});records.set(k,String(v))},
  removeItem:k=>records.delete(k)
 };
 const context=vm.createContext({
  window:{addEventListener(){},dispatchEvent(){}},
  document:{querySelectorAll:()=>[]},
  location:{reload(){reloads++}},Event:class{},setTimeout,clearTimeout
 });
 vm.runInContext(persistence,context);
 const controller=context.createMealPersistence(()=>base);
 controller.inspect(()=>{});
 return {controller,base,records,writes,failWith:fn=>{fail=fn},reloads:()=>reloads};
}
const snapshot={version:1,originalStorage:{mealRotationDataV1:'old'},replacement:{mealRotationDataV1:'new'},previousAttempts:[]};
{
 const e=environment({[journalKey]:'unreadable',mealRotationDataV1:'broken',mealRotationPlansV1:'broken',unrelated:'keep','mealRotationTestSandboxV1:fixture':'keep'});
 e.failWith(()=>true);
 e.controller.startFresh();
 assert.equal(e.writes.length,0,'Start Fresh must never write first');
 assert.equal(e.records.has(journalKey),false);
 assert.equal(e.records.has('mealRotationDataV1'),false);
 assert.equal(e.records.has('mealRotationPlansV1'),false);
 assert.equal(e.records.get('unrelated'),'keep');
 assert.equal(e.records.get('mealRotationTestSandboxV1:fixture'),'keep');
 assert.equal(e.controller.unsaved,false);
 assert.equal(e.reloads(),1);
}
{
 const e=environment();
 e.controller.testWriteJournal({...snapshot,previousAttempts:Array.from({length:12},(_,i)=>({...snapshot,createdAt:String(i)}))});
 const saved=JSON.parse(e.base.getItem(journalKey));
 assert.ok(saved.previousAttempts.length<=5);
 assert.ok(e.base.getItem(journalKey).length*2<=48000);
 assert.ok(saved.previousAttempts.every(item=>!item.previousAttempts));
}
{
 const e=environment();
 let attempts=0;
 e.failWith(key=>key===journalKey&&++attempts===1);
 assert.equal(e.controller.testWriteJournal({...snapshot,previousAttempts:[snapshot]}),true);
 assert.equal(attempts,2);
 assert.equal(JSON.parse(e.base.getItem(journalKey)).previousAttempts.length,0);
}
{
 const e=environment();
 e.failWith(key=>key===journalKey);
 assert.doesNotThrow(()=>e.controller.testWriteJournal(snapshot));
 assert.equal(e.writes.length,2,'Only one retry is allowed');
 assert.equal(e.base.getItem(journalKey),null);
 e.writes.length=0;
 e.controller.testWriteJournal({...snapshot,originalStorage:{mealRotationDataV1:'x'.repeat(50000)}});
 assert.equal(e.writes.length,0,'Oversized snapshots must be skipped, not truncated');
}
{
 const e=environment({mealRotationDataV1:'old'});
 e.failWith(key=>key===journalKey);
 assert.doesNotThrow(()=>e.controller.testReplace({mealRotationDataV1:'restored'}));
 assert.equal(e.base.getItem('mealRotationDataV1'),'restored');
 assert.equal(e.reloads(),1);
}
const context=vm.createContext({
 recipeInstructionReferenceResolver:()=>value=>value,
 recipeImportInstructionValue:r=>r.instructions||[],
 recipeImportTrelloBoard:()=>[]
});
vm.runInContext(imports.slice(imports.indexOf('function recipeImportItems('),imports.indexOf('function recipeImportMinutes(')),context);
vm.runInContext(state.slice(state.indexOf('function normalizeImportedBackup('),state.indexOf('function restoreBackupStorage(')),context);
const backup={
 version:2,cats:['Dinner'],active:'Dinner',
 meals:[{id:1,name:'Backup pasta',cat:'Dinner',ingredients:['pasta'],instructions:['Cook.'],rotation:true}],
 weekdayCategories:{Monday:['Dinner']},weekdayMealOverrides:{'Monday::Dinner':'1'},
 mealPlans:{activeId:'week',plans:[{id:'week',name:'Week',weekdayCategories:{Monday:['Dinner']},weekdayMealOverrides:{'Monday::Dinner':'1'}}]},
 cookSessions:{version:1,occurrences:{}},checkedIngredients:['pasta'],
 storage:{mealRotationExtensionV1:'opaque value',[journalKey]:'do not restore'}
};
const original=JSON.stringify(backup);
const items=context.recipeImportItems(backup);
assert.equal(items.length,1);
assert.equal(items[0].name,'Backup pasta');
assert.equal(JSON.stringify(context.recipeImportTags(items[0])),JSON.stringify(['Dinner']));
assert.equal(JSON.stringify(context.recipeImportTags({cat:['Dinner','Quick'],tags:['Easy']})),JSON.stringify(['Easy','Dinner','Quick']));
assert.equal(context.recipeImportItems({meals:backup.meals}).length,1);
const normalized=context.normalizeImportedBackup(backup);
for(const [field,key]of Object.entries({
 weekdayCategories:'mealRotationWeekdayCategoriesV1',weekdayMealOverrides:'mealRotationWeekdayMealOverridesV1',
 mealPlans:'mealRotationPlansV1',cookSessions:'mealRotationCookingSessionsV1',checkedIngredients:'mealRotationCheckedIngredientsV1'
}))assert.equal(normalized[key],JSON.stringify(backup[field]));
assert.equal(normalized.mealRotationDataV1,JSON.stringify({cats:backup.cats,active:backup.active,meals:backup.meals}));
assert.equal(normalized.mealRotationExtensionV1,'opaque value');
assert.equal(normalized[journalKey],undefined);
assert.equal(JSON.stringify(backup),original,'Import must not mutate the supplied backup');
console.log('PASS: quota-safe fresh reset, bounded journal and retry/skip, recovery restore, version-2 meals/categories/plans/progress/storage mapping.');
