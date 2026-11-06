// Run with: node --test tests/hidden-rotation-pins.test.cjs
// Browser replays cover allocation; these tests isolate source pin cleanup.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const key=(day,cat)=>day+'::'+cat;
const scheduled=(plan,day,cat)=>plan.weekdayCategories[day]?.includes(cat);
for(const filename of ['index.html','meal-rotation-test.html']){
 const source=fs.readFileSync(path.join(__dirname,'..',filename),'utf8');
 const start=source.indexOf('  // A temporary empty/one-time slot can conceal a real queued recipe.');
 const end=source.indexOf('  plan.weekdayMealOverrides=overrides;',start);
 assert.ok(start>=0&&end>start,'Hidden-slot release block must exist in '+filename);
 const block=new Function('plan','hiddenRotated','overrides','pins','choices','rotationGroupScheduled','weekdaySlotKey','manualWeekdayMealChoice',source.slice(start,end));
 const release=(plan,hidden,overrides,pins,choices)=>block(plan,hidden,overrides,pins,choices,scheduled,key,(p,day,cat,id)=>choices[key(day,cat)]?.substitution===true&&String(choices[key(day,cat)]?.mealId)===String(id));
 test(filename+': hidden automatic Sunday releases its pin without consuming the recipe',()=>{
  const plan={id:'original',weekdayCategories:{Sunday:['Weekend']}};
  const overrides={'Sunday::Weekend':'22',Sunday:'22','Saturday::Weekend':'537'};
  const pins={'Sunday::Weekend':'22','Saturday::Weekend':'537'};
  const choices={'Sunday::Weekend':{mealId:'22',retain:true},'Saturday::Weekend':{mealId:'537',retain:true}};
  release(plan,[{planId:'original',day:'Sunday',cat:'Weekend',meal:{id:'22'}}],overrides,pins,choices);
  assert.equal(overrides['Sunday::Weekend'],undefined);assert.equal(overrides.Sunday,undefined);assert.equal(pins['Sunday::Weekend'],undefined);
  assert.deepEqual(choices['Sunday::Weekend'],{parentId:'',blockedParents:[]});
  assert.equal(overrides['Saturday::Weekend'],'537');assert.equal(pins['Saturday::Weekend'],'537');
 });
 test(filename+': another plan is unaffected',()=>{
  const plan={id:'original',weekdayCategories:{Sunday:['Weekend']}},overrides={'Sunday::Weekend':'22'},pins={...overrides},choices={'Sunday::Weekend':{mealId:'22',retain:true}};
  release(plan,[{planId:'other',day:'Sunday',cat:'Weekend',meal:{id:'22'}}],overrides,pins,choices);
  assert.equal(overrides['Sunday::Weekend'],'22');assert.equal(pins['Sunday::Weekend'],'22');assert.equal(choices['Sunday::Weekend'].retain,true);
 });
 test(filename+': unassigned groups are unaffected',()=>{
  const plan={id:'original',weekdayCategories:{Sunday:['Weekend']}},overrides={'Sunday::Company':'535'},pins={...overrides},choices={'Sunday::Company':{mealId:'535',retain:true}};
  release(plan,[{planId:'original',day:'Sunday',cat:'Company',meal:{id:'535'}}],overrides,pins,choices);
  assert.equal(overrides['Sunday::Company'],'535');assert.equal(pins['Sunday::Company'],'535');assert.equal(choices['Sunday::Company'].retain,true);
 });
 for(const deferred of [undefined,['22'],['99']])test(filename+': explicit hidden manual choice stays'+(deferred?' with deferred metadata '+deferred[0]:''),()=>{
  const plan={id:'original',weekdayCategories:{Sunday:['Weekend']}},overrides={'Sunday::Weekend':'22'},pins={...overrides};
  const choices={'Sunday::Weekend':{mealId:'22',retain:true,substitution:true,...(deferred?{deferredMealIds:deferred}:{})}};
  const before=JSON.stringify({overrides,pins,choices});release(plan,[{planId:'original',day:'Sunday',cat:'Weekend',meal:{id:'22'}}],overrides,pins,choices);
  assert.equal(JSON.stringify({overrides,pins,choices}),before);
 });
 test(filename+': blocked linked parents survive automatic pin cleanup',()=>{
  const plan={id:'original',weekdayCategories:{Sunday:['Weekend']}},overrides={'Sunday::Weekend':'22'},pins={...overrides},choices={'Sunday::Weekend':{mealId:'22',retain:true,blockedParents:['99']}};
  release(plan,[{planId:'original',day:'Sunday',cat:'Weekend',meal:{id:'22'}}],overrides,pins,choices);
  assert.deepEqual(choices['Sunday::Weekend'],{parentId:'',blockedParents:['99']});
 });
}
