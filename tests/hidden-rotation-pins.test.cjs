// Run with: node --test tests/hidden-rotation-pins.test.cjs
// Focused regression for the hidden-slot pin release in index.html.
// This executes the actual source block, rather than a duplicate implementation.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const start=source.indexOf('  // A temporary empty/one-time slot can conceal a real queued recipe.');
const end=source.indexOf('  plan.weekdayMealOverrides=overrides;',start);
assert.ok(start>=0&&end>start,'Hidden-slot release block must exist');
const release=new Function('plan','hiddenRotated','overrides','pins','choices','rotationGroupScheduled','weekdaySlotKey',source.slice(start,end));
const key=(day,cat)=>day+'::'+cat;
const scheduled=(plan,day,cat)=>plan.weekdayCategories[day]?.includes(cat);
test('cycling a hidden Sunday Weekend recipe releases its saved pin',()=>{
 const plan={id:'original',weekdayCategories:{Sunday:['Weekend']}};
 const overrides={'Sunday::Weekend':'22',Sunday:'22','Saturday::Weekend':'537'};
 const pins={'Sunday::Weekend':'22','Saturday::Weekend':'537'};
 const choices={'Sunday::Weekend':{mealId:'22',retain:true},'Saturday::Weekend':{mealId:'537',retain:true}};
 release(plan,[{planId:'original',day:'Sunday',cat:'Weekend',meal:{id:'22'}}],overrides,pins,choices,scheduled,key);
 assert.equal(overrides['Sunday::Weekend'],undefined);
 assert.equal(overrides.Sunday,undefined);
 assert.equal(pins['Sunday::Weekend'],undefined);
 assert.deepEqual(choices['Sunday::Weekend'],{parentId:'',avoidMealId:'22',blockedParents:[]});
 assert.equal(overrides['Saturday::Weekend'],'537');
 assert.equal(pins['Saturday::Weekend'],'537');
});
test('hidden meals from another plan do not change this plan',()=>{
 const plan={id:'original',weekdayCategories:{Sunday:['Weekend']}};
 const overrides={'Sunday::Weekend':'22'},pins={'Sunday::Weekend':'22'},choices={'Sunday::Weekend':{mealId:'22',retain:true}};
 release(plan,[{planId:'other',day:'Sunday',cat:'Weekend',meal:{id:'22'}}],overrides,pins,choices,scheduled,key);
 assert.equal(overrides['Sunday::Weekend'],'22');
 assert.equal(pins['Sunday::Weekend'],'22');
});
test('hidden entries for unassigned groups do not clear unrelated saved choices',()=>{
 const plan={id:'original',weekdayCategories:{Sunday:['Weekend']}};
 const overrides={'Sunday::Company':'535'},pins={'Sunday::Company':'535'},choices={'Sunday::Company':{mealId:'535',retain:true}};
 release(plan,[{planId:'original',day:'Sunday',cat:'Company',meal:{id:'535'}}],overrides,pins,choices,scheduled,key);
 assert.equal(overrides['Sunday::Company'],'535');
 assert.equal(pins['Sunday::Company'],'535');
});
