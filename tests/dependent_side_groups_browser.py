"""Dependent assignments draw source recipes directly and follow their designated main."""
import copy,json
from collections import Counter
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose,rows
f.EXTRA+='''window.depTest={
 seed:(role=false)=>{cats.push('Grains','Tubers');for(const [id,name,cat] of [[101,'Rice one','Grains'],[102,'Rice two','Grains'],[103,'Rice three','Grains'],[104,'Rice idea','Grains'],[201,'Potato one','Tubers'],[202,'Potato two','Tubers']])meals.push({id,name,cat,rotation:id!==104,url:'',ingredients:['1 cup shared rice'],instructions:'Cook for 15 minutes.',notes:'Keep '+id,labels:['Legacy']});id=300;for(const [id,groups]of [[1,['Grains']],[2,['Tubers']],[3,['Grains','Tubers']]]){const m=meals.find(m=>m.id===id);m.preferredSideGroupIds=groups.map(group=>groupIdentity(group,true))}weekdayCategories.Saturday=['Sides','Mains','Weekend'];weekdayMealOverrides['Saturday::Sides']='20';weekdayMealOverrides['Saturday::Mains']='11';const p=mealPlans.find(p=>p.id===activePlanId);for(const [cat,n]of [['Sides',20],['Mains',11]]){p.cycleRetainedSlots['Saturday::'+cat]=String(n);p.cycleSlotChoices['Saturday::'+cat]={mealId:String(n),parentId:''}}saveWeekdayCategories();saveWeekdayMealOverrides();persist();if(role)setSideGroupPair(p,'Saturday','Sides','Weekend');renderList();slotTest.seed();promotionTest.check()},
 pair:parent=>setSideGroupPair(mealPlans.find(p=>p.id===activePlanId),'Saturday','Sides',parent),picker:()=>openDayCategoryPicker('Saturday'),
 prefs:(id,names)=>{assignSharedRecipeFields(meals.find(m=>m.id===id),{preferredSideGroupIds:names.map(n=>groupIdentity(n,true))});persist();renderList()},
 manual:(cat,n)=>applyManualWeekdayMeal('Saturday',cat,meals.find(m=>m.id===n)),cycle:(keys=['Saturday::Sides'],mark=false)=>moveDisplayedMealsToBottom(new Set(keys),false,mark),
 record:id=>meals.find(m=>m.id===id),order:cat=>meals.filter(m=>m.cat===cat).map(m=>m.id),
 link:(id,ids)=>{meals.find(m=>m.id===id).linkedMealIds=ids;persist();renderList()},
 weighted:()=>{meals.find(m=>m.id===104).rotation=true;assignSharedRecipeFields(meals.find(m=>m.id===101),{favorite:true});persist()},
 demote:ids=>{for(const id of ids)meals.find(m=>m.id===id).rotation=false;persist();renderList()},
 skip:(cat='Weekend')=>{const e=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat===cat);return skipScheduledMeal('Saturday',cat,e.meal)},
 promote:id=>promoteMealToRotation(meals.find(m=>m.id===id)),undo:()=>restoreState(JSON.parse(history.pop())),
 backup:()=>slotBackup.capture(),restore:s=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(s.mealRotationDataV1),storage:s}));backupRestoreReloadPending=true},
 oldRole:()=>{const p=mealPlans.find(p=>p.id===activePlanId);p.sideGroupPairs={Saturday:{[groupIdentity('Sides',true)]:groupIdentity('Weekend',true)}};delete p.dependentSideState;saveActiveMealPlan()},
 manualFlag:(cat='Sides')=>manualWeekdayMealChoice(mealPlans.find(p=>p.id===activePlanId),'Saturday',cat),
 sunday:()=>{weekdayCategories.Sunday=['Sides','Weekend'];saveWeekdayCategories();setSideGroupPair(mealPlans.find(p=>p.id===activePlanId),'Sunday','Sides','Weekend')},mainSunday:id=>applyManualWeekdayMeal('Sunday','Weekend',meals.find(m=>m.id===id)),rename:name=>renameCategoryDirect(name),normal:()=>{const m=meals.find(m=>m.id===1);delete m.preferredSideGroupIds;persist()},
 fail:(target='mealRotationPlansV1')=>{const original=Storage.prototype.setItem;let thrown=false;Storage.prototype.setItem=function(key,value){if(key.endsWith(target)&&!thrown){thrown=true;throw Error('simulated role write failure')}return original.call(this,key,value)};window.restoreDependentStorage=()=>{Storage.prototype.setItem=original}},oneMain:()=>{for(const m of meals)if(m.cat==='Weekend')m.rotation=m.id===1;delete weekdayCategories.Sunday;saveWeekdayCategories();persist()}
};'''
def setup(b,name,w=320,role=True):
 c,p,e,pr=f.setup(b,name,w,'multiple');p.evaluate('v=>depTest.seed(v)',role);return c,p,e,pr
def pick(p,cat='Sides',day='Saturday',plan='original'):
 return next((r['id'] for r in rows(p) if r['planId']==plan and r['day']==day and r['cat']==cat),None)
def rec(p,id):return p.evaluate('n=>depTest.record(n)',id)
def unchanged_checks(old,new):
 for id,s in new.items():assert s['checked']==(old[id]['checked'] if id in old else False),(id,s,old.get(id))
def automatic(b,name):
 c,p,e,pr=setup(b,name);assert pick(p)==101 and rec(p,101)['cat']=='Grains';assert all(m['cat']!='Sides' for m in state(p)['meals'] if m['id']>=100);before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);root=p.evaluate("depTest.order('Tubers')")
 p.evaluate('depTest.cycle()');assert pick(p)==102 and pick(p,'Weekend')==1 and p.evaluate("depTest.order('Tubers')")==root;assert not p.evaluate('depTest.manualFlag()');unchanged_checks(groceries,f.sources(p));p.evaluate('slotTest.back()');assert compose(p)==schedule
 p.evaluate("depTest.cycle(['Saturday::Weekend'])");assert pick(p,'Weekend')==3 and pick(p) in [201,202];assert pick(p,'Mains')==11 and pick(p,day='Wednesday',cat='Mains')==10 and pick(p,day='Sunday',cat='Weekend')==2;assert not p.evaluate('depTest.manualFlag()');unchanged_checks(groceries,f.sources(p))
 assert all(m.get('lastCooked')==next(x for x in before['meals'] if x['id']==m['id']).get('lastCooked') for m in state(p)['meals']);assert [p['weekdayCategories'] for p in state(p)['plans']]==[p['weekdayCategories'] for p in before['plans']];p.evaluate('slotTest.back()');assert compose(p)==schedule and not e,e
 print('PASS',name,'external unassigned source groups, designated main last in assignment order, source-only queues, main/side rotations, unchanged other slots/tabs/checks/dates/assignments, Cycle Back',flush=True);c.close()
def manual_and_ui(b,name,w):
 c,p,e,pr=setup(b,name,w);before=f.sources(p);p.evaluate("promotionTest.chooser('Saturday','Weekend')");d=p.locator('.weekday-meal-picker');d.locator('[data-meal-id="2"]').tap();d.get_by_role('button',name='Save',exact=True).tap();confirm=p.get_by_role('dialog',name='Spaghetti is already planned',exact=True);confirm.get_by_role('button',name='No — Keep both meals',exact=True).tap();assert pick(p,'Weekend')==2 and pick(p) in [201,202];unchanged_checks(before,f.sources(p))
 p.evaluate("depTest.manual('Sides',20)");assert pick(p)==20 and p.evaluate('depTest.manualFlag()');p.evaluate("depTest.manual('Mains',12)");assert pick(p)==20;p.reload();assert pick(p)==20 and p.evaluate('depTest.manualFlag()');p.evaluate("depTest.manual('Weekend',1)");assert pick(p) in [101,102,103] and not p.evaluate('depTest.manualFlag()') and rec(p,1)['preferredSideGroupIds'];p.evaluate("depTest.manual('Sides',201)");assert pick(p)==201;p.evaluate('depTest.cycle()');assert pick(p) in [101,102,103]
 p.evaluate('depTest.picker()');d=p.get_by_role('dialog',name="Choose Saturday's meal groups",exact=True);assert 'Dependent side' in d.get_by_role('button',name='Side for Sides',exact=True).inner_text();assert d.get_by_role('button',name='Side for Mains',exact=True).inner_text()=='Independent';d.get_by_role('button',name='Side for Sides',exact=True).tap();s=p.get_by_role('dialog',name='Side for Sides',exact=True);s.get_by_role('radio',name='Independent',exact=True).check();s.get_by_role('button',name='Cancel side for sides',exact=True).tap();assert 'Weekend' in d.get_by_role('button',name='Side for Sides',exact=True).inner_text();p.screenshot(path='/tmp/dependent-picker-'+name+'-'+str(w)+'.png');d.get_by_role('button',name='Close',exact=True).tap();assert p.evaluate('document.documentElement.scrollWidth<=innerWidth') and not e,e
 if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,w,'real chooser manual main change/duplicate confirmation coordinates side; manual outside-pool side survives unrelated changes/reload and expires on main change or side rotation; compact role selection/Cancel',flush=True);c.close()
def defaults_empty_history(b,name):
 c,p,e,pr=setup(b,name,role=False);assert pick(p)==20;original=compose(p);p.evaluate("depTest.manual('Weekend',2)");assert pick(p)==20;p.evaluate('depTest.pair("Weekend")');assert pick(p) in [201,202];p.evaluate('depTest.pair("")');kept=pick(p);assert kept in [201,202];p.evaluate("depTest.manual('Weekend',1)");assert pick(p)==kept;p.evaluate('depTest.cycle()');assert pick(p) in [20,21,22];assert not e,e;c.close()
 c,p,e,pr=setup(b,name);rice=[];roots=p.evaluate("depTest.order('Tubers')")
 for _ in range(2):rice.append(pick(p));p.evaluate('depTest.cycle()')
 assert rice==[101,102] and p.evaluate("depTest.order('Tubers')")==roots;p.evaluate("depTest.manual('Weekend',2)");assert pick(p)==201;p.evaluate("depTest.manual('Weekend',1)");assert pick(p)==101
 p.evaluate("depTest.prefs(2,[])");p.evaluate("depTest.manual('Weekend',2)");assert pick(p) in [20,21,22];p.evaluate("depTest.prefs(1,['Grains'])");p.evaluate('depTest.demote([101,102,103])');p.evaluate("depTest.manual('Weekend',1)");assert pick(p) is None and 'no compatible recipe' in p.locator('#list').inner_text();p.evaluate("depTest.manual('Weekend',3)");assert pick(p) in [201,202] and not e,e
 print('PASS',name,'independent defaults and disabling dependency, independent source histories across changes, no-preference fallback, empty pool explanation and recovery',flush=True);c.close()
def links_persistence(b,name):
 c,p,e,pr=setup(b,name);p.evaluate('depTest.link(2,[202])');p.evaluate("depTest.manual('Weekend',2)");assert pick(p)==202;assert len([r for r in rows(p) if r['day']=='Saturday' and r['planId']=='original' and r['id']==202])==1;assert not any(r['day']=='Saturday' and r['cat']=='Tubers' for r in rows(p));p.evaluate('depTest.cycle()');assert pick(p)==201,rows(p)
 backup=p.evaluate('depTest.backup()');expected=copy.deepcopy(state(p));schedule=compose(p);p.reload();actual=state(p);assert sorted(actual.pop('meals'),key=lambda m:m['id'])==sorted(expected['meals'],key=lambda m:m['id']) and actual=={k:v for k,v in expected.items() if k!='meals'} and compose(p)==schedule;p.evaluate("depTest.manual('Weekend',1)");p.evaluate('b=>depTest.restore(b)',backup);p.reload();assert compose(p)==schedule and sorted(state(p)['meals'],key=lambda m:m['id'])==sorted(expected['meals'],key=lambda m:m['id']) and state(p)['plans']==expected['plans'] and not e,e
 print('PASS',name,'explicit linked source fills dependent slot once without assigning/moving its group, side-only cycling preserves linked-parent suppression, reload and complete backup',flush=True);c.close()

def weighted_multiple_and_legacy(b,name):
 c,p,e,_=setup(b,name);p.evaluate('depTest.weighted()');seq=[]
 for _ in range(200):seq.append(pick(p));p.evaluate('depTest.cycle()')
 count=Counter(seq);assert count=={101:80,102:40,103:40,104:40},count;assert all(a!=b for a,b in zip(seq,seq[1:]));roots=p.evaluate("depTest.order('Tubers')");assert roots==[201,202];p.evaluate("depTest.manual('Weekend',3)");groups=[]
 for _ in range(12):groups.append(rec(p,pick(p))['cat']);p.evaluate('depTest.cycle()')
 assert set(groups)=={'Grains','Tubers'} and all(a!=b for a,b in zip(groups,groups[1:])),groups;assert not e,e
 print('PASS',name,'200 source-group weighted rotations retain 80:40:40:40 frequency without repeats/starvation; other group queue untouched; multiple preferred groups alternate with independent sequences',flush=True);c.close()
 c,p,e,_=setup(b,name,role=False);before=copy.deepcopy(state(p));old=compose(p);p.evaluate('depTest.oldRole()');p.reload();assert compose(p)==old and state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales'];p.evaluate("depTest.manual('Weekend',2)");assert pick(p) in [201,202] and not e,e
 print('PASS',name,'legacy configured pair without new state loads unchanged, preserving occurrence progress/scales; next real main change uses direct source pool',flush=True);c.close()
def promotion_skip_dates_and_single_main(b,name):
 c,p,e,_=setup(b,name);p.evaluate("depTest.prefs(5,['Tubers'])");p.evaluate('depTest.promote(5)');assert pick(p,'Weekend')==5 and pick(p) in [201,202];before=copy.deepcopy(state(p));p.evaluate("depTest.skip('Weekend')");assert pick(p,'Weekend')!=5 and all(m.get('lastCooked')==next(old for old in before['meals'] if old['id']==m['id']).get('lastCooked') for m in state(p)['meals']);assert not e,e;c.close()
 from scheduled_date_fixture import establish_dated_schedule
 c,p,e,_=setup(b,name);establish_dated_schedule(p);out=pick(p);p.evaluate("depTest.cycle(['Saturday::Weekend'],true)");assert rec(p,1)['lastCooked'].startswith('2026-10-31') and rec(p,out)['lastCooked'].startswith('2026-10-31');assert not rec(p,pick(p,'Weekend')).get('lastCooked') and not rec(p,pick(p)).get('lastCooked');p.evaluate('slotTest.back()');assert pick(p,'Weekend')==1 and pick(p)==out and not rec(p,out).get('lastCooked') and not e,e;c.close()
 c,p,e,_=setup(b,name);p.evaluate('depTest.oneMain()');p.evaluate("depTest.manual('Sides',201)");p.evaluate("depTest.cycle(['Saturday::Weekend'])");assert pick(p,'Weekend')==1 and pick(p) in [101,102,103] and not e,e
 print('PASS',name,'automatic promotion and Skip of main coordinate dependent side without cooking events; outgoing main+side receive their actual dated occurrence once, incoming recipes remain unmarked, Cycle Back restores; same-ID main rotation expires side override',flush=True);c.close()

def rename_progress_and_scopes(b,name):
 c,p,e,_=setup(b,name);before=copy.deepcopy(state(p));before_checks=f.sources(p);p.evaluate("depTest.rename('Sides')");d=p.get_by_role('dialog');d.get_by_role('textbox').fill('Side slot renamed');d.get_by_role('button',name='Save',exact=True).tap();assert pick(p,'Side slot renamed')==101 and not p.evaluate("depTest.manualFlag('Side slot renamed')")
 assert state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales'];unchanged_checks(before_checks,f.sources(p));p.evaluate("depTest.rename('Grains')");d=p.get_by_role('dialog');d.get_by_role('textbox').fill('Renamed rice');d.get_by_role('button',name='Save',exact=True).tap();assert rec(p,101)['cat']=='Renamed rice';p.evaluate("depTest.manual('Weekend',2)");assert pick(p,'Side slot renamed') in [201,202];p.evaluate("depTest.manual('Weekend',1)");assert pick(p,'Side slot renamed') in [102,103] and not e,e
 print('PASS',name,'renaming source and dependent-slot groups preserves pairing, progress, scales, grocery checks and source history; existing IDs and source memberships remain intact',flush=True);c.close()

def resulting_week_reservations(b,name):
 c,p,e,_=setup(b,name);p.evaluate("promotionTest.start('Sunday')");p.evaluate('depTest.sunday()');assert pick(p,day='Saturday')==101 and pick(p,day='Sunday')==201;p.evaluate('depTest.mainSunday(1)');assert pick(p,day='Saturday')==101 and pick(p,day='Sunday') in [102,103],rows(p);assert len([r for r in rows(p) if r['cat']=='Sides' and r['planId']=='original'])==2
 p.reload();assert pick(p,day='Saturday')==101 and pick(p,day='Sunday') in [102,103] and not e,e
 print('PASS',name,'Sunday-first new dependent selection reserves later Saturday side and avoids duplicates across the complete resulting week without changing retained slots',flush=True);c.close()

def linked_occurrence_reservations(b,name):
 c,p,e,_=setup(b,name);p.evaluate('depTest.link(2,[101])');p.evaluate('depTest.cycle()');assert pick(p)==102;p.evaluate('depTest.cycle()');assert pick(p)==103,rows(p);assert pick(p,'Grains','Sunday')==101 and not e,e;c.close()
 c,p,e,_=setup(b,name);p.evaluate('depTest.link(2,[201])');p.evaluate("depTest.manual('Weekend',3)");assert pick(p)==202 and pick(p,'Tubers','Sunday')==201 and not e,e
 print('PASS',name,'independent linked attachments elsewhere in the week reserve their recipe identities for both side rotation and manual-main coordination; retained linked meals remain unchanged',flush=True);c.close()

def repeated_progress_and_failure(b,name):
 c,p,e,_=setup(b,name);p.evaluate('depTest.demote([102,103])');p.evaluate('depTest.sunday()');p.evaluate('depTest.mainSunday(1)');assert pick(p,day='Saturday')==pick(p,day='Sunday')==101;p.evaluate('slotTest.seed()');p.evaluate('promotionTest.check()');before=copy.deepcopy(state(p));checks=f.sources(p);p.evaluate("depTest.manual('Weekend',2)");assert pick(p) in [201,202] and pick(p,day='Sunday')==101
 for key,entry in before['sessions']['occurrences'].items():
  if entry['context']['day']!='Saturday':assert state(p)['sessions']['occurrences'][key]==entry and state(p)['scales']['occurrences'][key]==before['scales']['occurrences'][key]
 unchanged_checks(checks,f.sources(p));assert not e,e;c.close()
 for role,target,parent in [(False,'mealRotationPlansV1','Weekend'),(True,'mealRotationDataV1','Mains')]:
  c,p,e,_=setup(b,name,role=role);before=copy.deepcopy(state(p));storage=p.evaluate('depTest.backup()');p.evaluate('t=>depTest.fail(t)',target)
  try:p.evaluate('v=>depTest.pair(v)',parent);raise AssertionError('Expected role write failure')
  except Exception as error:assert 'simulated role write failure' in str(error),str(error)
  assert state(p)==before and p.evaluate('depTest.backup()')==storage;p.evaluate('restoreDependentStorage()');assert not e,e;c.close()

 print('PASS',name,'repeated source recipe keeps independent Sunday progress/scales/checks when Saturday main+side change; failed role configuration rolls back queues, stable IDs, schedules, groceries and storage atomically',flush=True)

def partial_cycle_back(b,name):
 c,p,e,_=setup(b,name);old=compose(p);order=p.evaluate("depTest.order('Grains')");p.evaluate("depTest.cycle(['Saturday::Weekend'])");assert pick(p,'Weekend')==3 and pick(p) in [201,202];p.evaluate("slotTest.partial(['original||Saturday::Weekend'])");assert compose(p)==old and p.evaluate("depTest.order('Grains')")==order
 p.evaluate('depTest.cycle()');assert pick(p)==102;p.evaluate("slotTest.partial(['original||Saturday::Sides'])");assert compose(p)==old and not e,e
 print('PASS',name,'partial Cycle Back of main restores its exact dependent side and source queue; side-only partial restore accepts source recipes outside the assigned slot group',flush=True);c.close()

def empty_manual_chooser(b,name):
 c,p,e,_=setup(b,name);p.evaluate('depTest.demote([101,102,103])');p.evaluate('depTest.cycle()');assert pick(p) is None;preferences=rec(p,1)['preferredSideGroupIds'];p.get_by_role('button',name="Choose Saturday's Sides meal",exact=True).tap();d=p.locator('.weekday-meal-picker');d.locator('[data-meal-id="20"]').tap();d.get_by_role('button',name='Save',exact=True).tap();assert pick(p)==20 and rec(p,1)['preferredSideGroupIds']==preferences and p.evaluate('depTest.manualFlag()');p.evaluate('depTest.cycle()');assert pick(p) is None and not e,e
 print('PASS',name,'empty-slot explanation opens existing chooser; a manual outside-preference side can fill it without changing preferences, then expires on side rotation',flush=True);c.close()
def run_all():
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   automatic(b,name);defaults_empty_history(b,name);links_persistence(b,name);weighted_multiple_and_legacy(b,name);promotion_skip_dates_and_single_main(b,name);rename_progress_and_scopes(b,name);resulting_week_reservations(b,name);linked_occurrence_reservations(b,name);repeated_progress_and_failure(b,name);partial_cycle_back(b,name);empty_manual_chooser(b,name)
   for w in [320,360]:manual_and_ui(b,name,w)
  b.close()

if __name__=='__main__':run_all()
